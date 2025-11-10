#!/usr/bin/env node

/**
 * Quick Start Script for ACH Transfer Microservice
 * 
 * Usage:
 *   node start_ach_service.js
 * 
 * This script will:
 * 1. Check if dependencies are installed
 * 2. Verify configuration
 * 3. Start the ACH microservice
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Starting ACH Transfer Microservice...\n');

// Check if we're in the right directory
if (!fs.existsSync('src/ach_manager.js')) {
    console.error('❌ Error: ach_manager.js not found');
    console.log('   Please run this script from the project root directory');
    process.exit(1);
}

// Check if dependencies are installed
const nodeModulesPath = path.join(__dirname, 'src', 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
    console.log('📦 Installing dependencies...');
    exec('cd src && npm install', (error, stdout, stderr) => {
        if (error) {
            console.error('❌ Failed to install dependencies:', error.message);
            process.exit(1);
        }
        console.log('✅ Dependencies installed\n');
        startService();
    });
} else {
    startService();
}

function startService() {
    console.log('🔍 Checking configuration...\n');
    
    // Check environment variables
    const requiredEnvVars = [
        'PLAID_CLIENT_ID',
        'PLAID_SECRET',
        'DWOLLA_KEY',
        'DWOLLA_SECRET'
    ];
    
    const missingVars = requiredEnvVars.filter(v => !process.env[v]);
    
    if (missingVars.length > 0) {
        console.warn('⚠️  Warning: Missing environment variables:');
        missingVars.forEach(v => console.log(`   - ${v}`));
        console.log('\n   Please configure these in your .env file');
        console.log('   See config.env.example for reference\n');
    }
    
    console.log('🌟 Starting ACH Transfer Microservice on port 3000...\n');
    console.log('📝 Logs will appear below:\n');
    console.log('─'.repeat(60) + '\n');
    
    // Start the service
    const service = exec('cd src && node ach_manager.js');
    
    service.stdout.on('data', (data) => {
        process.stdout.write(data);
    });
    
    service.stderr.on('data', (data) => {
        process.stderr.write(data);
    });
    
    service.on('close', (code) => {
        console.log(`\n⚠️  Service exited with code ${code}`);
        process.exit(code);
    });
    
    // Graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n\n🛑 Shutting down ACH service...');
        service.kill();
        process.exit(0);
    });
}

console.log('✅ Setup complete! Starting ACH service...\n');
