const http = require('http');

http.get('http://localhost:5173/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    console.log('Status:', res.statusCode);
    console.log('Length:', data.length);
    console.log('Snippet:', data.slice(0, 300));
  });
}).on('error', err => console.error(err));
