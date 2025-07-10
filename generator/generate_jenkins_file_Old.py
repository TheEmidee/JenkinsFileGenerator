from uepyscripts import logger
from uepyscripts.context import project
from uepyscripts.context import engine
from uepyscripts.context import config
from uepyscripts.run import buildgraph
from uepyscripts.tools.algo.topological_order import Graph

import argparse
import json
from pathlib import Path
from mako.template import Template
from mako.lookup import TemplateLookup

class BuildNode:
    def __init__(
        self,
        json_node
    ):
        self.name = json_node['Name']
        self.depends_on : list[str] = []
        
        depends_on = json_node['DependsOn']
        if depends_on:
            self.depends_on = depends_on.split(';')

class BuildGroup:
    def __init__(
        self,
        json_node
    ):
        self.name = json_node['Name']
        self.nodes = []
        for node in json_node['Nodes']:
            self.nodes.append(BuildNode(node))

class BuildPlatform:
    def __init__(
        self,
        name : str
    ):
        self.name = name
        self.job_to_group : dict[str,str] = {}
        self.groups : dict[str,BuildGroup] = {}
        self.parallel_groups : list[list[str]] = []

    def parse_group(self,json_node):
        group = BuildGroup(json_node)
        self.groups.update( { group.name : group } )

        for node in group.nodes:
            self.job_to_group.update( { node.name : group.name } )

    def build_parallel_groups(self):
        g = Graph()

        for group_name, group in self.groups.items():
            for node in group.nodes:
                for dependency in node.depends_on:
                    required_group_name = self.job_to_group[dependency]
                    if required_group_name != group.name:
                        g.add_edge(group.name,required_group_name)

        self.parallel_groups = g.topological_sort_with_hierarchy()

class BuildContext:
    def __init__(
        self,
        json,
        buildgraph_properties : dict[str,str] = None 
    ):
        self.inlined_properties : str = ""
        self.platforms : dict[str,BuildPlatform] = {}

        if buildgraph_properties is not None:
            for key, value in buildgraph_properties.items():
                self.inlined_properties += f"-set:{key}={value} "

        for group in json['Groups']:
            platform_name = group['Agent Types'][0]
            
            build_platform : BuildPlatform = None
            if platform_name not in self.platforms:
                build_platform = BuildPlatform(platform_name)
                self.platforms[platform_name] = build_platform
            else:
                build_platform = self.platforms[platform_name]

            build_platform.parse_group(group)

        for name, platform in self.platforms.items():
            platform.build_parallel_groups()

class RenderContext:
    def __init__(
        self,
        jobs : str
        ):
        self.engine = engine
        self.project = project
        self.jobs = jobs
        self.config = config

TEMPLATE = """
def properties = "${ctx.inlined_properties}"

% for platform_name,platform in ctx.platforms.items():
    % for group_names in platform.parallel_groups:
        jobs = [:]

        % for group_name in group_names:
            jobs[ "${group_name}" ] = {
                runBuildGraph( 
                    "${group_name}", 
                    [ 
                        % for node in platform.groups[group_name].nodes:
                            "${node.name}",
                        % endfor
                    ],
                    "${platform_name}",
                    properties 
                    )
            }
        % endfor

        jobs.failFast = true
        parallel jobs
    % endfor
% endfor
"""

def read_json(
    path : Path
):
    with open(path) as f:
        return json.load(f)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a jenkisnfile based on command-line arguments.")
    parser.add_argument("--template", type=str, help="The name of the template to use")
    parser.add_argument("--target", type=str, default="", help="The buildgraph target name")
    parser.add_argument("--properties", type=str, default="", help="JSON string representing a dictionary with the properties to pass to buildgraph. Ex: {'key1': 'value1', 'key2': 'value2'}")
    args = parser.parse_args()

    template_file_name = args.template
    target = args.target
    properties = json.loads(args.properties) if args.properties else {}

    temp_folder = project.project_folders.saved_folders.temp
    temp_folder.mkdir(exist_ok=True)

    export_path = temp_folder.joinpath("buildgraph.json")

    extra_parameters = [
        f"-Export={export_path}",
        "uebp_UATMutexNoWait=1"
    ]

    output_folder = project.root_folder.joinpath(config["Jenkins"]["OutputFolder"])
    logger.info(f"Output folder : {output_folder}")
    if not output_folder.exists():
        raise Exception("The folder where to output the jenkinsfile does not exist")

    templates_folder = project.root_folder.joinpath(config["Jenkins"]["TemplatesFolder"])
    logger.info(f"TemplatesFolder : {templates_folder}")
    if not templates_folder.exists():
        raise Exception("The folder where to find the templates does not exist")

    template_path = templates_folder.joinpath(f"{template_file_name}.template")
    logger.info(f"TemplatePath : {template_path}")
    if not template_path.exists():
        raise Exception("Impossible to find the jenkins template file")

    buildgraph.run( target, properties, extra_parameters )
    json = read_json(export_path)
    build_context = BuildContext(json,properties)

    jobs_template = Template(TEMPLATE)
    jobs_output = jobs_template.render(ctx=build_context)

    template_lookup = TemplateLookup(directories=[templates_folder], output_encoding='utf-8', encoding_errors='replace')
    template = template_lookup.get_template(f"{template_file_name}.template")

    render_context = RenderContext(jobs_output)
    render = template.render(render_context=render_context)

    output_file = output_folder.joinpath(f"{template_file_name}_2")

    # open as binary because the output is in utf-8
    # required because if we output as text, all the EOL are doubled
    with open(output_file, "wb") as file:
        file.write(render)