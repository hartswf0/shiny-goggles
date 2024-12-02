#!/usr/bin/env python3

import re
import json
from typing import List, Dict, Any, Optional

class EntityParser:
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        """
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def parse_hierarchical_text(text: str) -> List[Dict[str, Any]]:
        """
        Advanced hierarchical text parsing with comprehensive information capture
        """
        # Patterns for different levels of hierarchy
        hierarchy_patterns = [
            r'^(\s*├──|\s*└──)\s*\[([^\]]+)\](.*)$',  # Level 1 items
            r'^(\s*│\s*├──|\s*│\s*└──)\s*\[([^\]]+)\](.*)$',  # Level 2 items
            r'^(\s*│\s*│\s*├──|\s*│\s*│\s*└──)\s*\[([^\]]+)\](.*)$',  # Level 3 items
        ]
        
        hierarchical_structure = []
        current_levels = [hierarchical_structure]
        
        for line in text.split('\n'):
            line = line.rstrip()
            if not line:
                continue
            
            # Try to match each hierarchy level
            matched = False
            for pattern in hierarchy_patterns:
                match = re.match(pattern, line)
                if match:
                    # Determine depth based on the prefix
                    depth = len(re.findall(r'│', match.group(1)))
                    
                    # Extract key components
                    marker = match.group(1).strip()
                    action = match.group(2).strip()
                    remaining_text = match.group(3).strip()
                    
                    # Create comprehensive hierarchy item
                    item = {
                        'marker': marker,
                        'action': action,
                        'full_text': f'[{action}] {remaining_text}',
                        'description': remaining_text,
                        'website_relevant': bool(remaining_text),
                        'children': []
                    }
                    
                    # Ensure we have enough levels in our current_levels list
                    while len(current_levels) <= depth:
                        current_levels.append([])
                    
                    # Add to the appropriate level
                    current_levels[depth].append(item)
                    
                    # If this is not the deepest level, add to parent's children
                    if depth > 0:
                        parent_level = current_levels[depth-1]
                        if parent_level:
                            parent_level[-1]['children'].append(item)
                    
                    matched = True
                    break
            
            # If no match found, reset hierarchy
            if not matched and line.strip():
                current_levels = [hierarchical_structure]
        
        return hierarchical_structure

    @staticmethod
    def extract_website_routes(text: str) -> List[Dict[str, Any]]:
        """
        Extract comprehensive website route information
        """
        # Regex to capture route-like structures
        route_pattern = re.compile(
            r'\[([^\]]+)\]\s*(.+)?', 
            re.MULTILINE
        )
        
        routes = []
        for match in route_pattern.finditer(text):
            route_info = {
                'route': match.group(1).strip(),
                'description': match.group(2).strip() if match.group(2) else '',
                'is_website_route': True
            }
            routes.append(route_info)
        
        return routes

    @staticmethod
    def parse_entities(file_path: str) -> Dict[str, Any]:
        """
        Advanced parsing of entities with comprehensive information capture
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Comprehensive regex patterns
        main_entity_pattern = re.compile(
            r'#<Entity:\s*([^>]+)>\n\s*Description:\s*"([^"]+)"(.*?)(?=\n#<Entity:|\Z)', 
            re.DOTALL
        )
        
        sub_entity_pattern = re.compile(
            r'<Entity:\s*([^>]+)>\n\s*Description:\s*"([^"]+)"(.*?)(?=\n<Entity:|\Z)', 
            re.DOTALL
        )
        
        morphism_pattern = re.compile(
            r'<Morphism:\s*([^>]+)>\n((?:\s*├── \[.*?\]\n)*)', 
            re.DOTALL
        )
        
        nested_entity_pattern = re.compile(
            r'<([^>]+):\s*([^>]+)>(?:\n\s*Description:\s*"([^"]*)")?([^<]*)', 
            re.DOTALL
        )
        
        action_pattern = re.compile(r'\[([^\]]+)\]')
        
        # Comprehensive parsing structure
        parsed_document = {
            'raw_text': content,
            'document_structure': [],
            'sitemap': {},
            'website_routes': []
        }
        
        # Extract website routes from entire document
        parsed_document['website_routes'] = EntityParser.extract_website_routes(content)
        
        # Find all main entities
        for main_match in main_entity_pattern.finditer(content):
            main_entity = {
                'type': 'main_entity',
                'name': main_match.group(1).strip(),
                'description': main_match.group(2).strip(),
                'raw_text': main_match.group(0),
                'sub_entities': [],
                'hierarchical_details': []
            }
            
            # Find ALL sub-entities within this main entity block
            for sub_match in sub_entity_pattern.finditer(main_match.group(3)):
                sub_entity = {
                    'type': 'sub_entity',
                    'name': sub_match.group(1).strip(),
                    'description': sub_match.group(2).strip(),
                    'raw_text': sub_match.group(0),
                    'morphisms': [],
                    'nested_entities': [],
                    'website_routes': []
                }
                
                # Find ALL morphisms for this sub-entity
                for morph_match in morphism_pattern.finditer(sub_match.group(3)):
                    morphism = {
                        'type': 'morphism',
                        'name': morph_match.group(1).strip(),
                        'raw_text': morph_match.group(0),
                        'actions': [
                            action.strip() 
                            for action in action_pattern.findall(morph_match.group(2))
                        ],
                        'hierarchical_details': EntityParser.parse_hierarchical_text(morph_match.group(2)),
                        'website_routes': EntityParser.extract_website_routes(morph_match.group(2))
                    }
                    sub_entity['morphisms'].append(morphism)
                
                # Extract website routes for this sub-entity
                sub_entity['website_routes'] = EntityParser.extract_website_routes(sub_match.group(3))
                
                # Find ALL nested entities within this sub-entity
                for nested_match in nested_entity_pattern.finditer(sub_match.group(3)):
                    nested_entity = {
                        'type': nested_match.group(1).strip(),
                        'name': nested_match.group(2).strip(),
                        'description': (nested_match.group(3) or '').strip(),
                        'raw_text': nested_match.group(0),
                        'morphisms': [],
                        'actions': [],
                        'website_routes': []
                    }
                    
                    # Find morphisms for nested entity
                    nested_context = nested_match.group(4)
                    for nested_morph_match in morphism_pattern.finditer(nested_context):
                        nested_morphism = {
                            'type': 'nested_morphism',
                            'name': nested_morph_match.group(1).strip(),
                            'raw_text': nested_morph_match.group(0),
                            'actions': [
                                action.strip() 
                                for action in action_pattern.findall(nested_morph_match.group(2))
                            ],
                            'hierarchical_details': EntityParser.parse_hierarchical_text(nested_morph_match.group(2)),
                            'website_routes': EntityParser.extract_website_routes(nested_morph_match.group(2))
                        }
                        nested_entity['morphisms'].append(nested_morphism)
                    
                    # Find direct actions in nested entity
                    nested_entity['actions'] = [
                        action.strip() 
                        for action in action_pattern.findall(nested_context)
                    ]
                    
                    # Extract website routes for nested entity
                    nested_entity['website_routes'] = EntityParser.extract_website_routes(nested_context)
                    
                    sub_entity['nested_entities'].append(nested_entity)
                
                main_entity['sub_entities'].append(sub_entity)
            
            # Create sitemap entry
            parsed_document['sitemap'][main_entity['name']] = {
                'description': main_entity['description'],
                'sub_pages': [sub['name'] for sub in main_entity['sub_entities']],
                'website_routes': EntityParser.extract_website_routes(main_match.group(0))
            }
            
            parsed_document['document_structure'].append(main_entity)
        
        return parsed_document

def main():
    input_file = '/Users/gaia/shiny-googles_S_BLU/shiny-goggles/index.html'
    output_file = '/Users/gaia/shiny-googles_S_BLU/shiny-goggles/parsed_entities.json'
    
    # Parse entities
    parsed_entities = EntityParser.parse_entities(input_file)
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(parsed_entities, f, indent=2)
    
    print(f"Parsed document structure saved to {output_file}")

if __name__ == '__main__':
    main()
