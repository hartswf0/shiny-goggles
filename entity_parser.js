// Entity parser and renderer with enhanced preprocessing
class EntityRenderer {
    constructor() {
        this.separator = '-'.repeat(56);
    }

    // Preprocess the content to make it more parse-friendly
    preprocessContent(content) {
        // Remove script and style tags
        content = content.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        content = content.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');

        // Normalize line breaks and remove extra whitespace
        content = content.replace(/\r\n/g, '\n');
        
        // Remove multiple consecutive empty lines
        content = content.replace(/\n{3,}/g, '\n\n');

        // Escape problematic characters while preserving XML-like tags
        content = this.escapeSpecialChars(content);

        return content;
    }

    // Escape special characters carefully
    escapeSpecialChars(content) {
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;')
            // Restore entity and morphism tags
            .replace(/&lt;Entity:/g, '<Entity:')
            .replace(/&lt;Morphism:/g, '<Morphism:')
            .replace(/&gt;/g, '>');
    }

    // Find blocks separated by the separator line
    extractBlocks(content) {
        // Preprocess first
        content = this.preprocessContent(content);

        const blocks = [];
        const lines = content.split('\n');
        let currentBlock = [];
        let inBlock = false;

        for (let line of lines) {
            // Trim the line
            line = line.trim();

            // Check for separator
            if (line === this.separator) {
                // If we were collecting a block, add it to blocks
                if (inBlock && currentBlock.length > 0) {
                    blocks.push(currentBlock.join('\n'));
                    currentBlock = [];
                }
                // Toggle block collection
                inBlock = !inBlock;
                continue;
            }

            // Collect lines when in a block
            if (inBlock) {
                // Skip completely empty lines
                if (line) {
                    currentBlock.push(line);
                }
            }
        }

        // Add last block if not empty
        if (currentBlock.length > 0) {
            blocks.push(currentBlock.join('\n'));
        }

        return blocks;
    }

    // Parse a single entity block
    parseEntityBlock(block) {
        const lines = block.split('\n');
        const entityData = {
            name: '',
            description: '',
            morphisms: [],
            children: []
        };

        let currentNode = entityData;
        let nodeStack = [entityData];
        let currentMorphism = null;

        for (let line of lines) {
            line = line.trim();

            // Entity tag
            const entityMatch = line.match(/<Entity:\s*([^>]+)>/);
            if (entityMatch) {
                const newEntity = {
                    name: entityMatch[1],
                    description: '',
                    morphisms: [],
                    children: []
                };
                
                // Add to parent's children
                nodeStack[nodeStack.length - 1].children.push(newEntity);
                nodeStack.push(newEntity);
                currentNode = newEntity;
                continue;
            }

            // Description
            const descMatch = line.match(/Description:\s*"([^"]+)"/);
            if (descMatch) {
                currentNode.description = descMatch[1];
                continue;
            }

            // Morphism tag
            const morphismMatch = line.match(/<Morphism:\s*([^>]+)>/);
            if (morphismMatch) {
                currentMorphism = {
                    name: morphismMatch[1],
                    actions: []
                };
                currentNode.morphisms.push(currentMorphism);
                continue;
            }

            // Morphism actions
            const actionMatch = line.match(/\[([^\]]+)\]/);
            if (actionMatch && currentMorphism) {
                currentMorphism.actions.push(actionMatch[1]);
            }
        }

        return entityData;
    }

    // Render entities to HTML
    renderEntityToHtml(entity, level = 0) {
        const indent = '  '.repeat(level);
        let html = `
            <div class="entity-card" data-level="${level}">
                <div class="entity-header">
                    <h${level + 2}>${entity.name}</h${level + 2}>
                    <p class="description">${entity.description}</p>
                </div>
                <div class="entity-content">`;

        // Render morphisms
        if (entity.morphisms.length > 0) {
            html += '<div class="morphisms">';
            for (const morphism of entity.morphisms) {
                html += `
                    <div class="morphism">
                        <h${level + 3}>${morphism.name}</h${level + 3}>
                        <ul>
                            ${morphism.actions.map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>`;
            }
            html += '</div>';
        }

        // Render children recursively
        if (entity.children.length > 0) {
            html += '<div class="children">';
            for (const child of entity.children) {
                html += this.renderEntityToHtml(child, level + 1);
            }
            html += '</div>';
        }

        html += '</div></div>';
        return html;
    }

    // Main render function
    render(content, targetElement) {
        // Extract blocks
        const blocks = this.extractBlocks(content);
        
        // Parse and render each block
        let html = '';
        for (const block of blocks) {
            const entityData = this.parseEntityBlock(block);
            html += this.renderEntityToHtml(entityData);
        }

        // Set the HTML
        targetElement.innerHTML = html;
    }
}

// Add default styles
const style = document.createElement('style');
style.textContent = `
    .entity-card {
        border: 1px solid #ddd;
        margin: 1rem;
        padding: 1rem;
        border-radius: 8px;
        background: #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .entity-header {
        border-bottom: 1px solid #eee;
        margin-bottom: 1rem;
    }

    .description {
        color: #666;
        font-style: italic;
        margin: 0.5rem 0;
    }

    .morphisms {
        margin-left: 1rem;
    }

    .morphism {
        margin: 1rem 0;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 4px;
    }

    .children {
        margin-left: 2rem;
    }

    .entity-card[data-level="0"] {
        border-left: 4px solid #007bff;
    }

    .entity-card[data-level="1"] {
        border-left: 4px solid #28a745;
    }

    .entity-card[data-level="2"] {
        border-left: 4px solid #dc3545;
    }

    .entity-card[data-level="3"] {
        border-left: 4px solid #ffc107;
    }
`;
document.head.appendChild(style);

// Initialize renderer
const renderer = new EntityRenderer();
