#!/usr/bin/env node

/**
 * Test script for MCP server
 * Sends test requests and validates responses
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function testMCPServer() {
  console.log('🧪 Testing Construction AI MCP Server...\n');

  // Start the server
  const server = spawn('node', [join(__dirname, 'dist/index.js')], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  let responseData = '';

  server.stdout.on('data', (data) => {
    responseData += data.toString();
  });

  server.stderr.on('data', (data) => {
    console.log('[Server Log]:', data.toString().trim());
  });

  // Wait for server to start
  await new Promise(resolve => setTimeout(resolve, 500));

  // Test 1: Initialize connection
  console.log('Test 1: Initialize connection');
  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {
        name: 'test-client',
        version: '1.0.0'
      }
    }
  };

  server.stdin.write(JSON.stringify(initRequest) + '\n');
  await new Promise(resolve => setTimeout(resolve, 500));
  console.log('✅ Initialize sent\n');

  // Test 2: List tools
  console.log('Test 2: List available tools');
  const listToolsRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  };

  server.stdin.write(JSON.stringify(listToolsRequest) + '\n');
  await new Promise(resolve => setTimeout(resolve, 500));
  console.log('✅ List tools sent\n');

  // Test 3: Call drywall_estimate tool
  console.log('Test 3: Call drywall_estimate tool');
  const estimateRequest = {
    jsonrpc: '2.0',
    id: 3,
    method: 'tools/call',
    params: {
      name: 'drywall_estimate',
      arguments: {
        walls: [
          {
            wall_id: 'North Wall',
            length_ft: 20,
            height_ft: 9,
            type: 'interior',
            openings: [
              { type: 'door', width: 3, height: 7, quantity: 1 }
            ]
          },
          {
            wall_id: 'South Wall',
            length_ft: 20,
            height_ft: 9,
            type: 'interior'
          },
          {
            wall_id: 'East Wall',
            length_ft: 15,
            height_ft: 9,
            type: 'interior',
            openings: [
              { type: 'window', width: 4, height: 3, quantity: 2 }
            ]
          },
          {
            wall_id: 'West Wall',
            length_ft: 15,
            height_ft: 9,
            type: 'interior'
          }
        ],
        ceilings: [
          {
            room: 'Main Room',
            type: 'standard',
            square_footage: 300,
            height_ft: 9
          }
        ],
        finish_level: 4,
        project_type: 'commercial'
      }
    }
  };

  server.stdin.write(JSON.stringify(estimateRequest) + '\n');
  await new Promise(resolve => setTimeout(resolve, 1000));
  console.log('✅ Estimate request sent\n');

  // Wait for all responses
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Parse responses
  console.log('\n📋 Server Responses:\n');
  const responses = responseData.trim().split('\n');

  responses.forEach((response, idx) => {
    try {
      const parsed = JSON.parse(response);
      console.log(`Response ${idx + 1}:`, JSON.stringify(parsed, null, 2).substring(0, 500));
      if (parsed.result && parsed.result.content) {
        console.log('\n📊 Estimate Output:\n');
        console.log(parsed.result.content[0].text);
      }
    } catch (e) {
      console.log(`Response ${idx + 1}: ${response.substring(0, 200)}`);
    }
  });

  // Cleanup
  server.kill();
  console.log('\n✅ Test completed!');
}

testMCPServer().catch(console.error);
