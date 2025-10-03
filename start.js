#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Smart Data Dashboard MVP...');
console.log('=====================================');

// Function to start a process
function startProcess(name, command, args, cwd) {
  console.log(`📦 Starting ${name}...`);
  
  const process = spawn(command, args, {
    cwd: cwd || process.cwd(),
    stdio: 'pipe',
    shell: true
  });

  process.stdout.on('data', (data) => {
    console.log(`[${name}] ${data.toString().trim()}`);
  });

  process.stderr.on('data', (data) => {
    console.error(`[${name}] ${data.toString().trim()}`);
  });

  process.on('close', (code) => {
    console.log(`[${name}] Process exited with code ${code}`);
  });

  return process;
}

// Start all processes
const processes = [];

// Start Backend (Python FastAPI)
processes.push(startProcess('Backend', 'python', ['-m', 'uvicorn', 'app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000']));

// Start Frontend (React)
processes.push(startProcess('Frontend', 'npm', ['run', 'dev'], path.join(__dirname, 'frontend')));

// Start Data Simulator (Python)
processes.push(startProcess('Simulator', 'python', ['simulator.py'], path.join(__dirname, 'data-simulator')));

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down all processes...');
  processes.forEach(proc => {
    if (proc && !proc.killed) {
      proc.kill('SIGINT');
    }
  });
  process.exit(0);
});

console.log('\n✅ All services starting...');
console.log('🌐 Frontend: http://localhost:3000');
console.log('🔌 Backend API: http://localhost:8000');
console.log('📚 API Docs: http://localhost:8000/docs');
console.log('\nPress Ctrl+C to stop all services');
