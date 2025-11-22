const { spawn } = require('child_process');
const path = require('path');

const hc = spawn('hc', ['sandbox', 'run', '-p', '8888']);

hc.stdout.on('data', (data) => {
    console.log(`stdout: ${data}`);
});

hc.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
});

hc.on('close', (code) => {
    console.log(`child process exited with code ${code}`);
});
