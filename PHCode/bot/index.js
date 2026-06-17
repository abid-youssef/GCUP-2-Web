const express = require('express');
const puppeteer = require('puppeteer');

const BASE   = process.env.TARGET || 'http://web:3000';
const SECRET = process.env.NOTE;
const PORT   = parseInt(process.env.PORT || '3001', 10);

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

async function visit(url) {
    const browser = await puppeteer.launch({
        headless: true,
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-popup-blocking',
        ],
    });

    try {
        const page = await browser.newPage();

        const origin = new URL(BASE);
        await page.setCookie({
            name:     'NOTE',
            value:    SECRET,
            domain:   origin.hostname,
            path:     '/',
            httpOnly: true,
            sameSite: 'Lax',
        });

        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 5000 }).catch(() => {});
        await new Promise(r => setTimeout(r, 45000));
    } finally {
        await browser.close();
    }
}

app.post('/visit', async (req, res) => {
    const url = req.body.url || req.query.url;

    if (!url) return res.status(400).json({ error: 'missing url' });

    try { new URL(url); } catch { return res.status(400).json({ error: 'invalid url' }); }

    res.json({ ok: true });
    visit(url).catch(() => {});
});

app.get('/visit', async (req, res) => {
    const url = req.query.url;

    if (!url) return res.status(400).send('missing url');

    try { new URL(url); } catch { return res.status(400).send('invalid url'); }

    res.send('ok');
    visit(url).catch(() => {});
});

app.listen(PORT, () => console.log(`bot on :${PORT}`));
