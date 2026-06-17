const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const DIR = path.join(__dirname, 'gallery');

app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/gallery', (req, res) => {
  res.json(fs.readdirSync(DIR));
});

app.get(/^\/download\/(.+)/, (req, res) => {
  const name = decodeURIComponent(req.params[0]);
  const p = path.join(DIR, name);
  res.download(p, err => {
    if (err && !res.headersSent) res.status(err.status || 404).end();
  });
});

app.listen(3000);
