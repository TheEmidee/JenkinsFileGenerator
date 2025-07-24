import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from mako.template import Template
from mako.exceptions import CompileException, SyntaxException
from mako.lookup import TemplateLookup
from mako import lexer, codegen, ast as mako_ast

from .. import logger
from .feature_registry import FeatureRegistry


@dataclass
class TemplateValidationMessage:
    """Represents a template validation error or warning"""
    level: str  # 'error', 'warning', 'info'
    message: str
    template_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None  # Surrounding code context
    suggestion: Optional[str] = None
    
    def __str__(self):
        location = ""
        if self.template_path:
            location += f"Template: {self.template_path}"
        if self.line_number:
            location += f", Line: {self.line_number}"
        if self.column:
            location += f", Column: {self.column}"
        
        result = f"[{self.level.upper()}] {self.message}"
        if location:
            result += f" ({location})"
        if self.context:
            result += f"\n  Context: {self.context}"
        if self.suggestion:
            result += f"\n  💡 Suggestion: {self.suggestion}"
        
        return result


class TemplateValidator:
    """Validates Mako template syntax and usage"""
    
    # Standard blocks that templates can define
    STANDARD_BLOCKS = {
        'libraries', 'imports', 'properties', 'pre_pipeline_steps',
        'build_steps', 'on_build_unstable', 'on_build_failure', 
        'on_build_success', 'post_build_steps', 'on_exception_thrown',
        'on_finally', 'additional_functions'
    }
    
    # Common variables available in template context
    STANDARD_CONTEXT_VARS = {
        'full_config', 'feature_config', 'global_values'
    }
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.messages: List[TemplateValidationMessage] = []
        self.template_lookup = TemplateLookup(directories=[str(templates_dir)])
    
    def validate_all_templates(self) -> List[TemplateValidationMessage]:
        """Validate all template files in the templates directory"""
        self.messages.clear()
        
        # Find all .mako files
        template_files = list(self.templates_dir.glob("*.mako"))
        
        if not template_files:
            self._add_message('warning', "No template files found", suggestion="Ensure template files have .mako extension")
            return self.messages
        
        logger.info(f"Validating {len(template_files)} template files...")
        
        for template_file in template_files:
            self._validate_template_file(template_file)
        
        # Validate template relationships
        self._validate_template_relationships()
        
        return self.messages
    
    def validate_template_for_feature(self, feature_name: str) -> List[TemplateValidationMessage]:
        """Validate a specific feature's template"""
        self.messages.clear()
        
        template_path = self.templates_dir / f"{feature_name}.mako"
        
        if not template_path.exists():
            self._add_message(
                'error', 
                f"Template file not found for feature '{feature_name}'",
                template_path=str(template_path),
                suggestion=f"Create {template_path} or check feature_name spelling"
            )
            return self.messages
        
        self._validate_template_file(template_path)
        return self.messages
    
    def _validate_template_file(self, template_path: Path):
        """Validate a single template file"""
        logger.debug(f"Validating template: {template_path}")
        
        try:
            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax validation
            self._validate_basic_syntax(template_path, content)
            
            # Mako compilation validation
            self._validate_mako_compilation(template_path, content)
            
            # Template structure validation
            self._validate_template_structure(template_path, content)
            
            # Context usage validation
            self._validate_context_usage(template_path, content)
            
            # Best practices validation
            self._validate_best_practices(template_path, content)
            
        except Exception as e:
            self._add_message(
                'error',
                f"Failed to validate template: {str(e)}",
                template_path=str(template_path)
            )
    
    def _validate_basic_syntax(self, template_path: Path, content: str):
        """Check for basic syntax issues"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for unmatched brackets/parentheses in Mako expressions
            if '${' in line:
                # Count opening and closing braces in expressions
                expressions = re.findall(r'\$\{[^}]*\}?', line)
                for expr in expressions:
                    if not expr.endswith('}'):
                        self._add_message(
                            'error',
                            "Unclosed Mako expression",
                            template_path=str(template_path),
                            line_number=i,
                            context=line.strip(),
                            suggestion="Ensure all ${...} expressions are properly closed"
                        )
            
            # Check for unmatched % blocks
            if line.strip().startswith('%'):
                if line.strip().startswith('% if') and 'endif' not in content[content.find(line):]:
                    # This is a simplified check - more sophisticated logic needed for real validation
                    pass
                
            # Check for common typos in def blocks
            def_match = re.match(r'<%def\s+name="([^"]+)"', line.strip())
            if def_match:
                def_name = def_match.group(1)
                # Check if def name contains common typos
                if def_name in self.STANDARD_BLOCKS and def_name != def_name.lower():
                    self._add_message(
                        'warning',
                        f"Block name case mismatch: '{def_name}' should be lowercase",
                        template_path=str(template_path),
                        line_number=i,
                        context=line.strip(),
                        suggestion=f"Use <%def name=\"{def_name.lower()}\"> instead"
                    )
    
    def _validate_mako_compilation(self, template_path: Path, content: str):
        """Validate that Mako can compile the template"""
        try:
            # Try to compile the template
            template = Template(content, filename=str(template_path))
            
            # Also test with template lookup (for includes/inheritance)
            try:
                template_from_lookup = self.template_lookup.get_template(template_path.name)
            except Exception as e:
                self._add_message(
                    'warning',
                    f"Template lookup failed: {str(e)}",
                    template_path=str(template_path),
                    suggestion="Check for missing template dependencies or includes"
                )
            
        except (CompileException, SyntaxException) as e:
            # Extract line number if available
            line_number = getattr(e, 'lineno', None)
            
            self._add_message(
                'error',
                f"Mako compilation error: {str(e)}",
                template_path=str(template_path),
                line_number=line_number,
                suggestion="Fix the Mako syntax error"
            )
        except Exception as e:
            self._add_message(
                'error',
                f"Template compilation failed: {str(e)}",
                template_path=str(template_path)
            )
    
    def _validate_template_structure(self, template_path: Path, content: str):
        """Validate template structure and def blocks"""
        # Find all def blocks
        def_blocks = re.findall(r'<%def\s+name="([^"]+)"[^>]*>', content)
        
        # Check for unknown blocks
        for block_name in def_blocks:
            if block_name not in self.STANDARD_BLOCKS:
                self._add_message(
                    'warning',
                    f"Unknown template block: '{block_name}'",
                    template_path=str(template_path),
                    suggestion=f"Standard blocks are: {', '.join(sorted(self.STANDARD_BLOCKS))}"
                )
        
        # Check for duplicate blocks
        seen_blocks = set()
        for block_name in def_blocks:
            if block_name in seen_blocks:
                self._add_message(
                    'error',
                    f"Duplicate template block: '{block_name}'",
                    template_path=str(template_path),
                    suggestion="Each block should be defined only once per template"
                )
            seen_blocks.add(block_name)
        
        # Check for orphaned closing tags
        if content.count('</%def>') != len(def_blocks):
            self._add_message(
                'error',
                "Mismatched <%def> and </%def> tags",
                template_path=str(template_path),
                suggestion="Ensure every <%def> has a corresponding </%def>"
            )
    
    def _validate_context_usage(self, template_path: Path, content: str):
        """Validate usage of context variables"""
        # Find all variable references
        var_references = re.findall(r'\$\{([^}]+)\}', content)
        var_references.extend(re.findall(r'%\s*(?:if|for|while)\s+([^:]+):', content))
        
        for var_ref in var_references:
            # Parse the variable reference
            var_parts = var_ref.split('.')
            root_var = var_parts[0].strip()
            
            # Remove common operators and keywords
            root_var = re.sub(r'^\s*(not\s+)?', '', root_var)
            root_var = root_var.split()[0] if root_var.split() else root_var
            
            # Check if it's a known context variable
            if (root_var not in self.STANDARD_CONTEXT_VARS and 
                not root_var.startswith(('loop', 'self', 'context', 'local')) and
                not root_var.isdigit() and
                root_var not in ['True', 'False', 'None'] and
                not root_var.startswith(("'", '"'))):
                
                self._add_message(
                    'warning',
                    f"Unknown context variable: '{root_var}'",
                    template_path=str(template_path),
                    suggestion=f"Standard context variables: {', '.join(sorted(self.STANDARD_CONTEXT_VARS))}"
                )
    
    def _validate_best_practices(self, template_path: Path, content: str):
        """Check for template best practices"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for very long lines
            if len(line) > 120:
                self._add_message(
                    'info',
                    f"Long line ({len(line)} characters)",
                    template_path=str(template_path),
                    line_number=i,
                    suggestion="Consider breaking long lines for better readability"
                )
            
            # Check for hardcoded values that should be configurable
            if re.search(r'(http://|https://|/[a-zA-Z0-9/]+)', line) and not line.strip().startswith('#'):
                self._add_message(
                    'info',
                    "Potential hardcoded path/URL detected",
                    template_path=str(template_path),
                    line_number=i,
                    context=line.strip(),
                    suggestion="Consider using configuration variables for paths and URLs"
                )
            
            # Check for missing error handling in Python code blocks
            if '<%' in line and ('raise' in line or 'Exception' in line):
                surrounding_lines = lines[max(0, i-3):i+3]
                if not any('try:' in l or 'except' in l for l in surrounding_lines):
                    self._add_message(
                        'info',
                        "Consider adding error handling",
                        template_path=str(template_path),
                        line_number=i,
                        suggestion="Wrap exception-prone code in try/except blocks"
                    )
    
    def _validate_template_relationships(self):
        """Validate relationships between templates"""
        # Check base template exists
        base_template = self.templates_dir / "base_jenkinsfile.mako"
        if not base_template.exists():
            self._add_message(
                'error',
                "Base template not found",
                template_path=str(base_template),
                suggestion="Create base_jenkinsfile.mako as the main template"
            )
            return
        
        # Check that all features have corresponding templates
        feature_registry = FeatureRegistry()
        available_features = feature_registry.get_all_features()
        
        for feature_name in available_features.keys():
            template_path = self.templates_dir / f"{feature_name}.mako"
            if not template_path.exists():
                self._add_message(
                    'warning',
                    f"No template found for feature '{feature_name}'",
                    template_path=str(template_path),
                    suggestion=f"Create {template_path} or the feature won't generate any code"
                )
    
    def _add_message(self, level: str, message: str, template_path: Optional[str] = None,
                    line_number: Optional[int] = None, column: Optional[int] = None,
                    context: Optional[str] = None, suggestion: Optional[str] = None):
        """Add a validation message"""
        self.messages.append(TemplateValidationMessage(
            level=level,
            message=message,
            template_path=template_path,
            line_number=line_number,
            column=column,
            context=context,
            suggestion=suggestion
        ))
    
    def has_errors(self) -> bool:
        """Check if there are any error-level messages"""
        return any(msg.level == 'error' for msg in self.messages)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning-level messages"""
        return any(msg.level == 'warning' for msg in self.messages)
    
    def print_messages(self, show_info: bool = True):
        """Print all validation messages with colors"""
        try:
            from colorama import Fore, Style, init
            init()
            
            colors = {
                'error': Fore.RED,
                'warning': Fore.YELLOW,
                'info': Fore.BLUE
            }
        except ImportError:
            colors = {'error': '', 'warning': '', 'info': ''}
            Style.RESET_ALL = ''
        
        for msg in self.messages:
            if not show_info and msg.level == 'info':
                continue
                
            color = colors.get(msg.level, '')
            print(f"{color}{msg}{Style.RESET_ALL}")
    
    def get_summary(self) -> str:
        """Get a summary of validation results"""
        error_count = sum(1 for msg in self.messages if msg.level == 'error')
        warning_count = sum(1 for msg in self.messages if msg.level == 'warning')
        info_count = sum(1 for msg in self.messages if msg.level == 'info')
        
        if error_count == 0 and warning_count == 0:
            return f"✅ All templates are valid! ({info_count} info messages)"
        elif error_count == 0:
            return f"⚠️  Templates are valid with {warning_count} warnings ({info_count} info messages)"
        else:
            return f"❌ Templates have {error_count} errors and {warning_count} warnings"


def validate_all_templates(templates_dir: Path, verbose: bool = True) -> bool:
    """
    Convenience function to validate all templates and print results.
    
    Args:
        templates_dir: Path to templates directory
        verbose: Whether to print info-level messages
        
    Returns:
        True if validation passed (no errors), False otherwise
    """
    validator = TemplateValidator(templates_dir)
    messages = validator.validate_all_templates()
    
    if messages:
        validator.print_messages(show_info=verbose)
        print(f"\n{validator.get_summary()}")
    
    return not validator.has_errors()


def validate_template_rendering(templates_dir: Path, sample_context: Dict[str, Any]) -> List[TemplateValidationMessage]:
    """
    Test template rendering with sample data to catch runtime errors.
    
    Args:
        templates_dir: Path to templates directory
        sample_context: Sample context data for testing
        
    Returns:
        List of validation messages
    """
    validator = TemplateValidator(templates_dir)
    messages = []
    
    template_files = list(templates_dir.glob("*.mako"))
    
    for template_file in template_files:
        try:
            template = validator.template_lookup.get_template(template_file.name)
            
            # Try to render each def block
            for block_name in validator.STANDARD_BLOCKS:
                try:
                    if hasattr(template.get_def(block_name), 'render'):
                        template.get_def(block_name).render(**sample_context)
                except AttributeError:
                    # Block doesn't exist - that's OK
                    pass
                except Exception as e:
                    messages.append(TemplateValidationMessage(
                        level='error',
                        message=f"Runtime error in block '{block_name}': {str(e)}",
                        template_path=str(template_file),
                        suggestion="Check template logic and context variable usage"
                    ))
                    
        except Exception as e:
            messages.append(TemplateValidationMessage(
                level='error',
                message=f"Failed to test template rendering: {str(e)}",
                template_path=str(template_file)
            ))
    
    return messages