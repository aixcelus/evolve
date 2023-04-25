#!/usr/bin/env node
/********************************************************************************
 *                          aiXcel.us API Integration License                   *
 *                    Copyright (c) 2023, aiXcelus www.aixcel.us                *
 *                                                                              *
 * Permission is hereby granted, free of charge, to any person obtaining a copy *
 * of this software and associated documentation files (the "Software"), to use,*
 * copy, modify, and distribute the Software, subject to the following          *
 * conditions:                                                                  *
 *                                                                              *
 * 1. The Software may only be used for the purpose of integrating the          *
 *    aiXcel.us API into the licensee's products.                               *
 * 2. The licensee is prohibited from modifying the Software to use an API or   *
 *    service from a competing provider, whether commercial or non-commercial.  *
 * 3. Redistributions of the Software must retain the above copyright notice    *
 *    and this permission notice.                                               *
 * 4. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS   *
 *    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF                *
 *    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT, AND   *
 *    THE AVAILABILITY OR RELIABILITY OF THE API. IN NO EVENT SHALL THE AUTHORS *
 *    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, *
 *    INCLUDING BUT NOT LIMITED TO DOWNTIME, ERRORS, OR INACCURACIES IN THE     *
 *    API, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   *
 *    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN *
 *    THE SOFTWARE.                                                             *
 * 5. The use of the aiXcel.us API is subject to the terms and conditions of    *
 *    the licensee's account license with aiXcel.us, which can be found at      *
 *    https://www.aixcel.us/tos.html.                                           *
 *                                                                              *
 * This license does not grant permission to use the trade names, trademarks,   *
 * service marks, or product names of aiXcel.us, except as required for         *
 * reasonable and customary use in describing the origin of the Software.       *
 * By using the Software, the licensee agrees to be bound by the terms and      *
 * conditions of this license.                                                  *
 ********************************************************************************/

const fs = require("fs");
const path = require("path");
const util = require("util");
const childProcess = require("child_process");
const axios = require("axios");
const fileType = require("file-type");
const mime = require("mime-types");
const tmp = require("tmp");
const pty = require("node-pty");

const URL = "https://aixcel.us/api/v1/evolve";

const mimeInterpreterMap = {
  "text/x-python": "python3",
  "text/x-shellscript": "bash",
  "text/x-perl": "perl",
  "text/x-ruby": "ruby",
  "text/javascript": "node",
  "application/x-php": "php",
  "text/x-csrc": "gcc",
  "text/x-c++src": "g++",
  "text/x-java": "java",
  "text/x-csharp": "csc",
  "text/x-fortran": "gfortran",
  "text/x-go": "go",
  "text/x-rustsrc": "rustc",
  "text/x-scala": "scala",
  "text/x-swift": "swift",
  "text/x-d": "dmd",
  "text/x-dylan": "dylan-compiler",
  "text/x-erlang": "erlc",
  "text/x-haskell": "ghc",
  "text/x-lisp": "sbcl",
  "text/x-lua": "lua",
  "text/x-objectivec": "clang",
  "text/x-objectivec++": "clang++",
  "text/x-pascal": "fpc",
  "text/x-prolog": "swipl",
  "text/x-r": "Rscript",
  "text/x-scheme": "guile",
  "text/x-tcl": "tclsh",
  "text/x-vb": "vbc",
  "text/x-ada": "gnatmake",
  "text/x-asm": "nasm",
  "text/x-cobol": "cobc",
  "text/x-diff": "diff",
  "text/x-dockerfile": "docker",
  "text/x-elixir": "elixir",
  "text/x-elm": "elm",
  "text/x-erlang": "erlc",
  "text/x-fsharp": "fsharpc",
  "text/x-haskell": "ghc",
  "text/x-ini": "ini",
  "text/x-julia": "julia",
  "text/x-kotlin": "kotlinc",
  "text/x-lua": "lua",
  "text/x-matlab": "matlab",
  "text/x-ocaml": "ocaml",
  "text/x-pascal": "fpc",
  "text/x-powershell": "pwsh",
  "text/x-rustsrc": "rustc",
  "text/x-sass": "sass",
  "text/x-scss": "sass",
  "text/x-sql": "sqlite3",
  "text/x-toml": "toml",
  "text/x-vb": "vbc",
  "text/x-yaml": "yml",
};

const errorPatterns = [
  /error/,
  /invalid/,
];

function checkForErrors(data) {
  return errorPatterns.some((pattern) => pattern.test(data));
}

function isExecutable(scriptPath) {
  return fs.promises
  .access(scriptPath, fs.constants.X_OK)
  .then(() => true)
  .catch(() => false);
}

function wrapScriptInMarkdown(scriptContent) {
return "```\n" + scriptContent + "```";
}

function extractScriptFromMarkdown(markdownContent) {
const match = markdownContent.match(/```(?:[a-zA-Z0-9]+)?\n([\s\S]*?)```/);
return match ? match[1] : markdownContent;
}

function getShebangForMimeType(mimeType) {
const interpreter = mimeInterpreterMap[mimeType];
return interpreter ? `#!/usr/bin/env ${interpreter}` : null;
}

async function ensureShebangForMimeType(scriptPath) {
const mimeType = mime.lookup(scriptPath);
const shebang = getShebangForMimeType(mimeType);

if (shebang) {
  const scriptContent = await fs.promises.readFile(scriptPath, "utf-8");
  if (!scriptContent.startsWith("#!")) {
    await fs.promises.writeFile(scriptPath, shebang + "\n" + scriptContent);
  }
}
}

async function runScript(runtime, scriptPath, scriptArgs) {
let fixedAttempt = 1;
let backupCreated = false;

while (true) {
  const executable = await isExecutable(scriptPath);
  await ensureShebangForMimeType(scriptPath);

  const command = executable ? [scriptPath] : [runtime, scriptPath];
  const args = scriptArgs.slice();
  const ptyProcess = pty.spawn(command[0], command.slice(1).concat(args), {
    name: "xterm-color",
    cols: 80,
    rows: 30,
  });

  let data = "";
  ptyProcess.on("data", (chunk) => {
    data += chunk;
  });

  const exitStatus = await new Promise((resolve) => {
    ptyProcess.on("exit", resolve);
  });

  if (exitStatus === 0 && !checkForErrors(data)) {
    break;
  } else {
    console.error(`Error: Script crashed with the following error:\n${data}`);
    const scriptContent = await fs.promises.readFile(scriptPath, "utf-8");
    const wrappedScript = wrapScriptInMarkdown(scriptContent);
    const json_data = {
      scriptFile: wrappedScript,
      crashLog: data,
    };
    console.log("Getting help...");
    const response = await axios.post(URL, json_data);
    if (response.status === 200) {
      const markdownContent = response.data;
      const rewrittenScript = extractScriptFromMarkdown(markdownContent);
      console.log(`Corrected Script:\n${rewrittenScript}`);

      if (!backupCreated) {
        const backupScriptPath = scriptPath + ".backup";
        await fs.promises.writeFile(backupScriptPath, scriptContent);
        console.log(`Original script backed up as '${backupScriptPath}'`);
        backupCreated = true;
      }

      await fs.promises.writeFile(scriptPath, rewrittenScript);
      console.log(`Corrected script saved as: ${scriptPath}`);
    }
  }
}
}

(async () => {
console.log("evolve.js (v1.0) - aiXcelus Evolve Client Starting...");
const args = process.argv.slice(2);
if (args.length < 1) {
  console.log("Usage: evolve.js [runtime] <path_to_script> [args...]");
  process.exit(1);
}

const scriptPath = path.resolve(args[0]);
const runtime = await isExecutable(scriptPath) ? null : args.shift();
const scriptArgs = args.slice();

if (!fs.existsSync(scriptPath)) {
    console.error(`Error: File '${scriptPath}' does not exist`);
    process.exit(1);
  }

  await runScript(runtime, scriptPath, scriptArgs);
})();
