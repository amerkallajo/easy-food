// Build in place with pinned dependencies; no scratch-directory resolution is needed.
const path = require('node:path');
require('esbuild').buildSync({
  absWorkingDir: __dirname,
  entryPoints: ['viewer.src.js'],
  outfile: path.join(__dirname, 'viewer.bundle.js'),
  bundle: true,
  minify: true,
  format: 'iife',
});
console.log('Built viewer.bundle.js');
