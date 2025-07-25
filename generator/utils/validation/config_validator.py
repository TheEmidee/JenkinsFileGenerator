from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

import yaml

from generator.utils.validation.base_validator import BaseValidator, ValidationMessage
from generator.core.feature_registry import FeatureRegistry
from generator.core.pipeline_config import PipelineConfig

@dataclass
class ConfigValidationMessage(ValidationMessage):
    def get_context_output_name(self) -> str:
        return "Field"

class LineTrackingDict(dict):
    """Dictionary that tracks line numbers for YAML parsing"""
    def __init__(self, data, line_map=None):
        super().__init__(data)
        self._line_map = line_map or {}
    
    def get_line_number(self, key_path: str) -> Optional[int]:
        """Get line number for a given key path like 'features.git.use_simple_checkout'"""
        return self._line_map.get(key_path)

class LineTrackingLoader(yaml.SafeLoader):
    """YAML loader that tracks line numbers for each key"""
    
    def __init__(self, stream):
        super().__init__(stream)
        self.line_map = {}
        self.key_stack = []
    
    def construct_mapping(self, node, deep=False):
        # Track line numbers for keys in this mapping
        self._track_mapping_lines(node)
        
        # Get the normal mapping result
        result = super().construct_mapping(node, deep)
        
        # Convert to LineTrackingDict if this is the root mapping
        if not self.key_stack:  # Root level
            return LineTrackingDict(result, self.line_map)
        else:
            return result
    
    def _track_mapping_lines(self, node):
        """Track line numbers for all keys in a mapping node"""
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=False)
            if isinstance(key, str):
                # Build the full path for this key
                current_path = '.'.join(self.key_stack + [key])
                self.line_map[current_path] = key_node.start_mark.line + 1
                
                # If the value is a mapping, recurse with updated stack
                if isinstance(value_node, yaml.MappingNode):
                    self.key_stack.append(key)
                    self._track_mapping_lines(value_node)
                    self.key_stack.pop()

class ConfigValidator(BaseValidator):
    """Enhanced configuration validator with detailed error reporting"""
    
    def __init__(self, config_path: Path):
        super(ConfigValidator, self).__init__()
        self.config_path : Path = config_path
        self.raw_config: Optional[LineTrackingDict] = None
    
    def _validate_internal(self ):
        self._validate_file_exists()
        self._validate_yaml_syntax()
        self._validate_schema()
        self._validate_features()

    def _get_validation_identifier(self) -> str:
        return "Configuration"
    
    def _get_file_path(self) -> Path:
        return self.config_path
    
    def _validate_file_exists(self):
        """Check if config file exists and is readable"""
        if not self.config_path.exists():
            self._add_message('error', f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        if not self.config_path.is_file():
            self._add_message('error', f"Path is not a file: {self.config_path}")
            raise ValueError(f"Not a file: {self.config_path}")
    
    def _validate_yaml_syntax(self):
        """Validate YAML syntax and load with line tracking"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for common YAML issues first
            self._check_yaml_common_issues(content)
            
            # Load with line tracking
            raw_config = yaml.load(content, Loader=LineTrackingLoader)
            
            if raw_config is None:
                self._add_message('error', "Configuration file is empty")
                raise ValueError("Empty configuration file")
                
        except yaml.YAMLError as e:
            line_no = getattr(e, 'problem_mark', None)
            if line_no:
                self._add_message(
                    'error', 
                    f"YAML syntax error: {e.problem}",
                    line_number=line_no.line + 1,
                    column=line_no.column + 1
                )
            else:
                self._add_message('error', f"YAML syntax error: {str(e)}")
            raise
    
    def _check_yaml_common_issues(self, content: str):
        """Check for common YAML formatting issues"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for tabs (should use spaces)
            if '\t' in line:
                self._add_message(
                    'warning',
                    "Found tab character. YAML should use spaces for indentation",
                    line_number=i,
                    suggestion="Replace tabs with spaces (typically 2 or 4 spaces per indent level)"
                )
            
            # Check for trailing spaces
            if line.rstrip() != line and line.strip():
                self._add_message(
                    'warning',
                    "Found trailing whitespace",
                    line_number=i,
                    suggestion="Remove trailing spaces from the end of the line"
                )
    
    def _validate_schema(self):
        """Validate against the main PipelineConfig schema"""
        try:
            with open(self.config_path, 'r') as f:
                yaml_contents = yaml.safe_load(f)
                validated_config = PipelineConfig(**yaml_contents)
                self.validated_config = validated_config                
            
        except ValidationError as e:
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                line_number = None
                
                # Safely get line number
                if hasattr(self.raw_config, 'get_line_number'):
                    line_number = self.raw_config.get_line_number(field_path)
                
                message = self._format_pydantic_error(error, field_path)
                suggestion = self._get_error_suggestion(error, field_path)
                
                self._add_message(
                    'error',
                    message,
                    line_number=line_number,
                    context=field_path,
                    suggestion=suggestion
                )
    
    def _validate_features(self):
        """Validate each feature's configuration"""
        if not hasattr(self, 'validated_config'):
            return  # Skip if schema validation failed
        
        feature_registry = FeatureRegistry()
        
        for feature_name, feature_config in self.validated_config.features.items():
            # Check if feature exists
            available_features = feature_registry.get_all_features()
            if feature_name not in available_features:
                line_number = self.raw_config.get_line_number(f'features.{feature_name}') if self.raw_config else None
                
                similar_features = self._find_similar_feature_names(feature_name, available_features.keys())
                suggestion = f"Available features: {', '.join(available_features.keys())}"
                if similar_features:
                    suggestion = f"Did you mean: {', '.join(similar_features)}? " + suggestion
                
                self._add_message(
                    'error',
                    f"Unknown feature: '{feature_name}'",
                    line_number=line_number,
                    context=f'features.{feature_name}',
                    suggestion=suggestion
                )
                continue
            
            # Validate feature configuration
            try:
                feature_class = available_features[feature_name]
                feature_instance = feature_class()
                feature_instance.get_feature_config(self.validated_config)
                
            except ValidationError as e:
                for error in e.errors():
                    field_path = f'features.{feature_name}.' + '.'.join(str(loc) for loc in error['loc'])
                    line_number = self.raw_config.get_line_number(field_path) if self.raw_config else None
                    
                    message = self._format_pydantic_error(error, field_path)
                    suggestion = self._get_error_suggestion(error, field_path)
                    
                    self._add_message(
                        'error',
                        f"Feature '{feature_name}': {message}",
                        line_number=line_number,
                        context=field_path,
                        suggestion=suggestion
                    )
            except Exception as e:
                self._add_message(
                    'error',
                    f"Feature '{feature_name}' validation failed: {str(e)}",
                    context=f'features.{feature_name}'
                )
    
    def _format_pydantic_error(self, error: Dict[str, Any], field_path: str) -> str:
        """Format a Pydantic validation error into a readable message"""
        error_type = error.get('type', 'unknown')
        input_value = error.get('input')
        
        if error_type == 'missing':
            return f"Required field is missing"
        elif error_type == 'string_type':
            return f"Expected string, got {type(input_value).__name__}: {input_value}"
        elif error_type == 'bool_parsing':
            return f"Expected boolean (true/false), got: {input_value}"
        elif error_type == 'int_parsing':
            return f"Expected integer, got: {input_value}"
        elif error_type == 'value_error':
            return f"Invalid value: {error.get('msg', str(input_value))}"
        else:
            return error.get('msg', f'Validation error: {error_type}')
    
    def _get_error_suggestion(self, error: Dict[str, Any], field_path: str) -> Optional[str]:
        """Get helpful suggestions for common validation errors"""
        error_type = error.get('type', 'unknown')
        
        if error_type == 'missing':
            if 'channel' in field_path:
                return "Add a channel field like: channel: \"#ci-builds\""
            elif 'name' in field_path:
                return "Add a name field with your project name"
        
        elif error_type == 'bool_parsing':
            return "Use true or false (lowercase, no quotes)"
        
        elif error_type == 'string_type':
            return "Wrap the value in quotes if it contains special characters"
        
        elif 'url' in field_path.lower():
            return "Ensure the URL starts with http:// or https://"
        
        return None
    
    def _find_similar_feature_names(self, target: str, available: List[str]) -> List[str]:
        """Find feature names similar to the target (simple similarity)"""
        similar = []
        target_lower = target.lower()
        
        for feature in available:
            feature_lower = feature.lower()
            
            # Check for substring matches
            if target_lower in feature_lower or feature_lower in target_lower:
                similar.append(feature)
            # Check for common prefixes/suffixes
            elif (target_lower.startswith(feature_lower[:3]) or 
                  feature_lower.startswith(target_lower[:3])) and len(target) > 3:
                similar.append(feature)
        
        return similar[:3]  # Return top 3 matches