// Run with the bundled Node runtime. All temporary output stays under runs/_cache/.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { buildDeck } from './deck_content.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const option=(name)=>{const i=process.argv.indexOf(name);if(i<0||!process.argv[i+1])throw new Error(`Required option ${name}`);return path.resolve(process.argv[i+1]);};
const runtimeModules=option('--runtime-node-modules');
process.env.RUNTIME_NODE_MODULES=runtimeModules;
const runtimePython=option('--runtime-python');
const skillDir=option('--skill-dir');
const outputPptx=option('--output-pptx');
const buildDir=path.join(root,'runs/_cache/presentation_build');
await fs.mkdir(buildDir,{recursive:true});
await fs.mkdir(path.dirname(outputPptx),{recursive:true});
const runtimeRequire=createRequire(path.join(runtimeModules,'../package.json'));
const {Presentation,PresentationFile}=await import(pathToFileURL(runtimeRequire.resolve('@oai/artifact-tool')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
const data=JSON.parse(await fs.readFile(path.join(root,'slides/presentation_data.json'),'utf8'));
for(const im of data.images){const bytes=await fs.readFile(path.join(root,im.path));if(crypto.createHash('sha256').update(bytes).digest('hex')!==im.sha256)throw new Error('Image checksum mismatch');im.bytes=Array.from(bytes);}
if(data.talk.reduce((a,b)=>a+b.seconds,0)>270||data.script_word_count>450)throw new Error('Talk budget exceeded');
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
buildDeck(presentation,data);
const candidatePath=path.join(buildDir,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const result=await finalizePresentation({
  workspaceDir:root,candidatePath,finalPath:outputPptx,pythonExecutable:runtimePython,
  integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,4,5,8,9,10].flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:12,
  requiredNativeTableOwnerSlides:[3,4,5,8,9,10],requiredNativeChartOwnerSlides:[4,6],
  materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(buildDir,'validation.json'),
});
await fs.writeFile(path.join(buildDir,'export_result.json'),JSON.stringify(result,null,2));
for(let i=0;i<presentation.slides.items.length;i++){
  const png=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(buildDir,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
// Native PowerPoint export also checks the final package in the target application.
await fs.writeFile(path.join(buildDir,'presentation_source.json'),JSON.stringify(presentation.toProto()));
console.log(JSON.stringify({slides:presentation.slides.items.length,outputPptx,wordCount:data.script_word_count,plannedSeconds:data.talk.reduce((a,b)=>a+b.seconds,0)}));
