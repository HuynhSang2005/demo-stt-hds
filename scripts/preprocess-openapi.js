#!/usr/bin/env node
/**
 * Preprocess OpenAPI specification for better TypeScript client generation
 * Cleans up operation IDs to generate nicer method names
 */

const fs = require('fs');
const path = require('path');

const OPENAPI_FILE = path.join(__dirname, '..', 'openapi.json');

function preprocessOpenAPI() {
    try {
        console.log('🔧 Preprocessing OpenAPI specification...');
        
        // Read the OpenAPI spec
        const openApiContent = JSON.parse(fs.readFileSync(OPENAPI_FILE, 'utf8'));
        
        let operationsProcessed = 0;
        
        // Process all paths and operations
        for (const pathKey in openApiContent.paths) {
            const pathData = openApiContent.paths[pathKey];
            
            for (const method in pathData) {
                if (pathData[method].operationId) {
                    const operation = pathData[method];
                    const originalId = operation.operationId;
                    
                    // Remove tag prefix if it exists (websocket_get_websocket_status -> get_websocket_status)
                    let newOperationId = originalId;
                    if (operation.tags && operation.tags.length > 0) {
                        const tag = operation.tags[0];
                        const tagPrefix = `${tag}_`;
                        if (originalId.startsWith(tagPrefix)) {
                            newOperationId = originalId.substring(tagPrefix.length);
                        }
                    }
                    
                    // Apply the cleaned operation ID
                    if (newOperationId !== originalId) {
                        operation.operationId = newOperationId;
                        operationsProcessed++;
                        console.log(`  ✓ ${originalId} -> ${newOperationId}`);
                    }
                }
            }
        }
        
        // Write back the processed spec
        fs.writeFileSync(OPENAPI_FILE, JSON.stringify(openApiContent, null, 2));
        
        console.log(`✅ Preprocessed ${operationsProcessed} operations`);
        console.log(`📁 Updated: ${OPENAPI_FILE}`);
        
    } catch (error) {
        console.error('❌ Error preprocessing OpenAPI spec:', error.message);
        process.exit(1);
    }
}

// Run preprocessing
preprocessOpenAPI();