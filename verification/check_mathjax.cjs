// Read a JSON array on stdin and validate every formula independently.
const fs = require('node:fs');
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');
const {SerializedMmlVisitor} = require('mathjax-full/js/core/MmlTree/SerializedMmlVisitor.js');

RegisterHTMLHandler(liteAdaptor());
// GitHub disables these packages. Also disable noundefined locally so an
// unknown control sequence fails instead of being printed in red.
const disabled = new Set(['noerrors', 'noundefined', 'bbox', 'html', 'require',
  'newcommand', 'action', 'colortbl']);
const tex = new TeX({packages: AllPackages.filter(p => !disabled.has(p)),
  maxMacros: 1000, formatError: (_jax, error) => { throw error; }});
const document = mathjax.document('', {InputJax: tex, OutputJax: new SVG()});
const visitor = new SerializedMmlVisitor();
const formulas = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = formulas.map(item => {
  try {
    // Compile each expression separately; definitions cannot leak between notes.
    tex.reset();
    const math = new document.options.MathItem(item.tex, tex, item.display);
    math.start.node = document.adaptor.body(document.document);
    math.setMetrics(16, 8, 80 * 16, 1000000, 1);
    math.compile(document);
    const mml = visitor.visitTree(math.root);
    if (mml.includes('<merror')) throw new Error(mml);
    return {id: item.id, status: 'passed'};
  } catch (error) {
    return {id: item.id, status: 'failed', error: error.message};
  }
});
process.stdout.write(JSON.stringify({version: mathjax.version, results}));
