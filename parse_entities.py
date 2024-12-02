#!/usr/bin/env python3

import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path

@dataclass
class Morphism:
    name: str
    actions: List[str]
    
@dataclass
class Entity:
    name: str
    description: str
    morphisms: List[Morphism]
    children: List['Entity']
    depth: int

class EntityParser:
    def __init__(self, content: str):
        self.content = content
        self.current_pos = 0
        self.entities: Dict[str, Entity] = {}
        
    def find_negative_space(self) -> List[tuple[int, int]]:
        """Find blocks of whitespace that separate entities"""
        spaces = []
        lines = self.content.split('\n')
        start = None
        
        for i, line in enumerate(lines):
            if not line.strip():
                if start is None:
                    start = i
            elif start is not None:
                spaces.append((start, i))
                start = None
                
        return spaces
    
    def extract_entity_blocks(self) -> List[str]:
        """Extract entity blocks using negative space as separators"""
        blocks = []
        current_block = []
        in_entity = False
        entity_depth = 0
        
        for line in self.content.split('\n'):
            stripped = line.strip()
            if not stripped:
                if current_block and entity_depth == 0:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    in_entity = False
                continue
                
            # Track entity depth using tree characters
            if '<Entity:' in line:
                in_entity = True
                entity_depth += 1
            elif in_entity:
                if '└──' in line and not any(x in line for x in ['<Entity:', '<Morphism:']):
                    entity_depth = max(0, entity_depth - 1)
                elif '├──' in line and '<Entity:' not in line:
                    # Keep track of sibling entities
                    pass
                
            if in_entity:
                current_block.append(line)
                
        if current_block:
            blocks.append('\n'.join(current_block))
            
        return blocks

    def parse_entity(self, block: str) -> Optional[Entity]:
        """Parse a single entity block with improved tree structure handling"""
        lines = block.split('\n')
        # Handle both standard and tree-style entity headers with improved regex
        entity_match = re.search(r'(?:[│├└](?:──)?\s*)?<Entity:\s*([^>]+)>|^[\s│]*(?:├──|└──)\s*<([^>]+)>', lines[0])
        if not entity_match:
            return None
            
        name = (entity_match.group(1) or entity_match.group(2)).strip()
        description = ""
        morphisms = []
        children = []
        
        # Count leading spaces and tree characters for depth
        depth = len(re.match(r'^[\s│├└─]*', lines[0]).group())
        
        current_morphism = None
        in_description = False
        
        for line in lines[1:]:
            if 'Description:' in line:
                in_description = True
                desc_match = re.search(r'Description:\s*"([^"]*)"', line)
                if desc_match:
                    description = desc_match.group(1)
                else:
                    description = line.split('Description:', 1)[1].strip().strip('"')
            elif in_description and line.strip().startswith('"'):
                # Handle multi-line descriptions
                description += ' ' + line.strip().strip('"')
            elif '<Morphism:' in line or re.search(r'[│├└](?:──)?\s*<Morphism:', line):
                in_description = False
                if current_morphism:
                    morphisms.append(current_morphism)
                morph_match = re.search(r'<Morphism:\s*([^>]+)>', line)
                if morph_match:
                    morph_name = morph_match.group(1)
                    current_morphism = Morphism(morph_name, [])
            elif current_morphism and re.search(r'[│├└](?:──)?\s*\[', line):
                # Extract action text after tree formatting with improved regex
                action_match = re.search(r'[│├└](?:──)?\s*\[(.*?)\]|[│├└](?:──)?\s*(.*?)$', line)
                if action_match:
                    action = action_match.group(1) or action_match.group(2)
                    if action:
                        current_morphism.actions.append(action.strip())
                    
        if current_morphism:
            morphisms.append(current_morphism)
            
        return Entity(name, description, morphisms, children, depth)

    def build_entity_tree(self):
        """Build hierarchical tree of entities"""
        blocks = self.extract_entity_blocks()
        entities = []
        
        for block in blocks:
            entity = self.parse_entity(block)
            if entity:
                entities.append(entity)
        
        # Build hierarchy based on indentation depth
        root_entities = []
        stack = []
        
        for entity in entities:
            while stack and stack[-1].depth >= entity.depth:
                stack.pop()
            
            if stack:
                stack[-1].children.append(entity)
            else:
                root_entities.append(entity)
                
            stack.append(entity)
            
        return root_entities
    
    def print_entity_tree(self, entities: List[Entity], level: int = 0):
        """Print the entity tree in a readable format"""
        for entity in entities:
            indent = "  " * level
            print(f"{indent}{'└──' if level > 0 else ''} Entity: {entity.name}")
            if entity.description:
                print(f"{indent}    Description: {entity.description}")
            
            for morphism in entity.morphisms:
                print(f"{indent}    ├── Morphism: {morphism.name}")
                for action in morphism.actions:
                    print(f"{indent}    │   ├── {action}")
                    
            if entity.children:
                self.print_entity_tree(entity.children, level + 1)
                
def main():
    input_file = Path("/Users/gaia/shiny-googles_S_BLU/shiny-goggles/index.html")
    with open(input_file, 'r') as f:
        content = f.read()
        
    parser = EntityParser(content)
    root_entities = parser.build_entity_tree()
    parser.print_entity_tree(root_entities)
    
if __name__ == "__main__":
    main()
