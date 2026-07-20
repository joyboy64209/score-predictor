const path = require('path');
const packager = require('electron-packager');

async function main() {
  const output = await packager({
    dir: path.resolve(__dirname, '..'),
    name: 'Match Predictor',
    platform: 'win32',
    arch: 'x64',
    out: path.resolve(__dirname, '..', 'release'),
    overwrite: true,
    prune: true,
    asar: true,
    executableName: 'Match Predictor',
    ignore: [
      /^\/backend(\/|$)/,
      /^\/ml(\/|$)/,
      /^\/docs(\/|$)/,
      /^\/data(\/|$)/,
      /^\/release(\/|$)/,
      /^\/\.git(\/|$)/,
      /^\/frontend\/node_modules(\/|$)/,
      /^\/backend\/node_modules(\/|$)/,
      /^\/ml\/\.venv(\/|$)/,
    ],
  });

  // eslint-disable-next-line no-console
  console.log(`Packaged desktop app: ${output[0]}`);
}

main().catch((error) => {
  // eslint-disable-next-line no-console
  console.error(error);
  process.exit(1);
});