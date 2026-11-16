// One shared builder for the live review and the editable file export.
export function buildDeck(presentation, data) {
  if (presentation.slides.items.length) presentation.slides.delete(presentation.slides.items.map((_, i) => i));
  presentation.slideSize = { width: 1280, height: 720 };
  const C = { bg: '#F8FAF8', ink: '#14343A', muted: '#52686C', green: '#137D70', light: '#E6F1ED', blue: '#456889', amber: '#9C5526', white: '#FFFFFF' };
  const font = 'Arial';
  function text(slide, value, x, y, w, h, size=28, color=C.ink, bold=false) {
    const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    s.text=value; s.text.insets=0; s.text.style={fontFamily:font,fontSize:size,color,bold}; return s;
  }
  function page(title, owner, backup=false) {
    const s=presentation.slides.add(); s.background.fill=C.bg;
    text(s,title,64,48,1152,90,42,C.ink,true);
    const n=presentation.slides.items.length;
    text(s,backup?'Backup for questions':`SDSC6021  /  ${owner}`,64,678,1060,22,17,C.muted);
    text(s,String(n).padStart(2,'0'),1160,678,56,22,17,C.muted);
    return s;
  }
  function table(s, values, x,y,w,h,widths,size=24) {
    const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
    t.styleOptions={headerRow:true,bandedRows:false};
    t.borders.assign({fill:'#D6E1DD',width:0.65,style:'solid'});
    t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:C.white,textStyle:{fontFamily:font,fontSize:size,color:C.ink},margins:{left:12,right:10,top:10,bottom:8}});
    t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.ink,textStyle:{fontFamily:font,fontSize:size,color:C.white,bold:true}});
    return t;
  }
  function chart(s,categories,values,x,y,w,h,colors,max=100) {
    return s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories,
      series:[{name:'Accuracy (%)',values,fill:C.green,points:values.map((_,idx)=>({idx,fill:colors?.[idx]??C.green})),valuesFormatCode:'0.00'}],
      barOptions:{direction:'column',grouping:'clustered',gapWidth:85},hasLegend:false,
      dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{typeface:font,fontSize:22,bold:true,fill:C.ink}},
      xAxis:{textStyle:{typeface:font,fontSize:20,fill:C.muted},line:{fill:'#B7C7C2',width:1}},
      yAxis:{min:0,max,majorUnit:20,title:{text:'Top-1 accuracy (%)',textStyle:{typeface:font,fontSize:18,fill:C.muted}},textStyle:{typeface:font,fontSize:18,fill:C.muted},majorGridlines:{fill:'#DCE5E1',width:0.6}},chartFill:C.bg,plotAreaFill:C.bg});
  }
  function notes(s,i) { s.speakerNotes.text=`${data.talk[i].owner}. Target ${data.talk[i].seconds} seconds.\n\n${data.talk[i].script}\n\nSources:\n${data.talk[i].sources.join('\n')}`; }

  // 1. Title and user problem.
  let s=presentation.slides.add(); s.background.fill=C.ink;
  text(s,'When Does\nSynthetic Data Help?',76,150,1110,220,68,C.white,true);
  text(s,'A generation, training and validation toolkit\nfor image classification with 20 real images per class',80,405,1100,108,30,'#D3E9E0');
  text(s,'CityU SDSC6021  /  Product/Application',80,637,1000,34,22,'#D3E9E0'); notes(s,0);

  // 2. A concrete recorded workflow.
  s=page('A complete workflow with saved evidence','A');
  const cols=[64,461,858];
  [['INPUT: CIFAR-10 CASE','10 class names\n20 real images per class'],['TOOL','Generate and select\nExtract frozen features\nTrain linear heads'],['OUTPUT','Saved models\nReal-test predictions\nAccuracy and timing']].forEach((v,i)=>{text(s,v[0],cols[i],155,355,34,23,C.green,true);text(s,v[1],cols[i],203,355,115,27);});
  text(s,'Recorded run: 2,000 candidates, 15 classifiers, 160,000 test predictions',64,330,1150,45,26,C.ink,true);
  data.images.forEach((img,i)=>{s.images.add({blob:new Uint8Array(img.bytes).buffer,contentType:'image/png',alt:`Generated ${img.class_name}, ${img.image_id}`,fit:'contain',position:{left:64+i*270,top:405,width:200,height:200}});text(s,img.class_name,64+i*270,614,220,28,20,C.muted);});
  text(s,'Examples from our\nSD1.5 candidate pool',900,450,300,100,27,C.muted); notes(s,1);

  // 3. Conditions and treatment definition.
  s=page('Five conditions share the same real samples','B');
  table(s,[['Condition','Synthetic / class','Selection'],['Real only','0','None'],['Random 50','50','Fixed random ranking'],['CLIP 50','50','CLIP target-class ranking'],['Random 150','150','Fixed random ranking'],['CLIP 150','150','CLIP target-class ranking']],64,160,760,365,[230,200,330],24);
  text(s,'20 real images per class\n3 paired seeds\n10,000 real test images',865,175,350,150,28,C.ink,true);
  text(s,'Frozen ResNet-18 and BN\nIdentical head initialization\nIdentical real sampling\n500 updates for every head',865,350,350,175,25,C.muted);
  text(s,'Training objective: real only = Lreal     mixed = 0.5 Lreal + 0.5 Lsynthetic',64,558,1150,40,25,C.ink,true);
  text(s,'Same real-image count, different source weights. The comparison evaluates this fixed mixing strategy.',64,612,1150,38,21,C.muted); notes(s,2);

  // 4. Formal effects, with SD shown explicitly in an editable table.
  s=page('Synthetic data improved the matched baseline','C');
  chart(s,['Real only','Random 50','CLIP 50','Random 150','CLIP 150'],data.summary.map(r=>r.mean_accuracy_pct),54,155,740,400,[C.blue,C.green,C.green,C.green,C.green],85);
  table(s,[['Condition','Mean ± SD (%)','Gain (pp)'],...data.summary.map((r,i)=>[data.conditionNames[i],`${r.mean_accuracy_pct.toFixed(2)} ± ${r.sd_accuracy_pct.toFixed(2)}`,i?`+${r.paired_gain_pp.toFixed(2)}`:'Baseline'])],820,180,397,354,[138,158,101],20);
  text(s,'+3.62 to +3.84 pp across the four mixed conditions',64,565,1150,46,32,C.green,true);
  text(s,'Official test results. Means and sample SD across 3 paired seeds. SD is not a confidence interval.',64,625,1150,32,20,C.muted); notes(s,3);

  // 5. Retention versus compute, with the shared generation cost visible.
  s=page('More retained images added little benefit','C');
  table(s,[['Paired comparison','Mean change (pp)'],['CLIP − Random, 50 / class','+0.20'],['CLIP − Random, 150 / class','+0.20'],['150 − 50 / class, Random','−0.02'],['150 − 50 / class, CLIP','−0.02']],64,180,690,310,[470,220],27);
  text(s,'48.14 min',825,185,390,80,62,C.green,true);
  text(s,'Recorded production + evaluation',825,278,390,70,25,C.muted);
  text(s,'42.52 min',825,375,390,70,45,C.ink,true);
  text(s,'Candidate generation\n88.3% of recorded stage time',825,455,390,85,25,C.muted);
  text(s,'No observed mean gain from retaining 150 / class',64,555,1150,45,32,C.ink,true);
  text(s,'One shared pool of 2,000 candidates. Retaining fewer images did not reduce its generation cost.\nStage totals exclude setup, development, human work and transfers. Small differences are descriptive.',64,612,1150,60,20,C.muted); notes(s,4);

  // 6. The alternative is a product decision, not an augmentation-controlled comparison.
  s=page('Zero-shot CLIP is stronger on this benchmark','C');
  chart(s,['Best trained condition\nCLIP 50, mean of 3 seeds','Zero-shot CLIP\nSingle reference'],[75.28,88.21],64,165,735,420,[C.green,C.blue],100);
  text(s,'A simpler alternative\nneeds consideration',850,205,355,125,34,C.ink,true);
  text(s,'Different pretrained model\nand inference procedure',850,355,355,90,27,C.muted);
  text(s,'Our augmentation improves\nthe specified ResNet baseline.\nIt does not establish the best\nclassifier for this dataset.',850,480,355,130,25,C.muted); notes(s,5);

  // 7. Human audit and self-test have distinct evidence boundaries.
  s=page('Author testing exposed an interpretation gap','D');
  text(s,'100-image label audit',64,175,540,45,33,C.green,true);
  text(s,'Two completed forms\n100 / 100 class judgements agree',64,250,540,105,30);
  text(s,'Target classes were recognizable.\nStructural defects can remain.\nThis does not certify overall image quality.',64,390,535,150,27,C.muted);
  text(s,'Author self-test',690,175,525,45,33,C.green,true);
  text(s,'14 / 14 functional checks pass',690,250,525,50,30);
  text(s,'“I can repeat the numbers,\nbut cannot read the conclusion.”',690,325,525,110,31,C.ink,true);
  text(s,'We added readable condition definitions\nand separate loss terms. External user\nusability remains untested.',690,480,525,130,26,C.muted);
  text(s,'The 40-image smoke run checks function and reproduction. Formal results use the separate 10,000-image test set.',64,625,1150,35,20,C.muted); notes(s,6);

  // 8. A real contribution, bounded claims and team responsibilities.
  s=page('A reproducible toolkit with bounded conclusions','D');
  text(s,'Contribution',64,165,570,45,31,C.green,true);
  text(s,'A working, traceable workflow\nand a controlled case study',64,232,600,100,38,C.ink,true);
  text(s,'One dataset and one label budget\nThree seeds share one synthetic pool\nNo equal-real-weight control\nExternal usability still untested',64,385,610,185,27,C.muted);
  table(s,[['Role','Responsibility'],['A','Engineering and generation'],['B','Data and classification'],['C','Selection and evaluation'],['D','Product and delivery']],720,180,495,315,[90,405],25);
  text(s,'Prior work studies synthetic augmentation\nand CLIP filtering: He et al. (2023).\nOur contribution is a reproducible tool\nand its evaluated scope.',720,530,490,120,23,C.muted);
  notes(s,7);

  // 9. Backup: original smoke counts and post-hoc loss semantics.
  s=page('Backup: smoke results and loss definitions','A / B',true);
  table(s,[['Smoke condition','Correct / dev','Real train CE','Synthetic CE'],...data.selfTest.results.map(r=>[r.condition_id,`${r.correct} / ${r.dev_count}`,r.real_train_ce_all_four_views_posthoc.toFixed(3),r.selected_synthetic_ce_all_four_views_posthoc==null?'—':r.selected_synthetic_ce_all_four_views_posthoc.toFixed(3)])],64,165,1152,340,[330,250,280,292],26);
  text(s,'16 real training images + 4 internal dev images per class. One dev image = 2.5 pp.',64,535,1150,40,26,C.ink,true);
  text(s,'CE is a post-hoc full-training calculation over 4 views. Logged loss is a final-minibatch value.\nAll four exact paired McNemar p-values are 1.0. This small smoke run supports no benefit claim.\nThe same fixed-setting outputs match the earlier smoke. It adds no independent repetition.',64,594,1150,75,21,C.muted);
  s.speakerNotes.text='Backup only. Do not include in the five-minute talk. Source: shared/synthetic_v2/audits/author_self_test/verification.json. The mixed objective changes the real loss coefficient from 1.0 to 0.5. No new training or official test evaluation was run for these diagnostics.';

  // 10. Backup: per-class effects from the official analysis.
  s=page('Backup: class effects vary','C',true);
  const classTable=table(s,[['Class','CLIP 50 accuracy (%)','Gain vs real only (pp)'],...data.perClass.map(r=>[r.class_name,r.mean_accuracy_pct.toFixed(2),`${r.mean_gain_pp>=0?'+':''}${r.mean_gain_pp.toFixed(2)}`])],64,150,1152,450,[330,400,422],24);
  classTable.cells.block({row:0,column:0,rowCount:11,columnCount:3}).assign({margins:{left:12,right:10,top:5,bottom:4}});
  text(s,'Official test, 3 paired seeds. These differences do not establish a causal mechanism.',64,630,1150,35,22,C.muted);
  s.speakerNotes.text='Backup only. Source: shared/synthetic_v2/c_evaluation/tables/08_g4_per_class.csv, condition clip_50. Deer mean gain 12.467 pp, automobile -1 pp, ship -1.967 pp. No coverage or regularisation mechanism is established.';

  // 11. Backup: practical reproduction, transparent failed precision check.
  s=page('Backup: reproducibility and known limitations','A / B / C',true);
  text(s,'Released evidence',64,175,540,42,32,C.green,true);
  text(s,'Fixed configuration and model seal\n2,000-image candidate pool\n15 trained heads and input manifests\n160,000 official test predictions\nIndependent B and C audits',64,247,555,250,28);
  text(s,'Known limitation',690,175,525,42,32,C.amber,true);
  text(s,'CPU/GPU feature discrepancy\nexceeded the original strict threshold',690,247,525,100,31,C.ink,true);
  text(s,'Max absolute difference: 2.01 × 10⁻⁴\nOriginal threshold: 1 × 10⁻⁵\nTraining-reference predictions unchanged\nLimited diagnostic supports a precision cause\nNo claim of full test-set equivalence',690,385,525,210,25,C.muted);
  const link=text(s,'github.com/kanekikenny/sdsc6021-synthetic-data-toolkit',64,620,1140,40,25,C.green,true);link.hyperlink={uri:data.repository,isExternal:true};
  s.speakerNotes.text='Backup only. Sources: report/B_v04_review.md, report/B_C_G4_cross_review.md, shared/synthetic_v2/audits/b_pr3_precision_diagnostic.json. Preserve the failed strict comparison. Reference-prediction agreement concerns training samples, not independently rerun official tests. Raw logs stay local when they include private machine details.';

  // 12. References.
  s=page('Backup: sources and project records','D',true);
  const refs=[['Rombach et al. (2022)','High-Resolution Image Synthesis with Latent Diffusion Models','https://arxiv.org/abs/2112.10752'],['Radford et al. (2021)','Learning Transferable Visual Models From Natural Language Supervision','https://proceedings.mlr.press/v139/radford21a.html'],['He et al. (2023)','Is Synthetic Data from Generative Models Ready for Image Recognition?','https://arxiv.org/abs/2210.07574']];
  refs.forEach((r,i)=>{let y=165+i*135;text(s,r[0],64,y,1150,32,28,C.green,true);text(s,r[1],64,y+42,1150,38,26);const l=text(s,r[2],64,y+82,1150,30,21,C.muted);l.hyperlink={uri:r[2],isExternal:true};});
  text(s,'Project data: C G4 tables and figures, B independent reviews, human annotation records, author self-test audit',64,599,1150,62,22,C.muted);
  s.speakerNotes.text='Backup only. Sources were checked on 2026-11-16. The cited papers establish the pretrained components and prior synthetic-augmentation work. All reported experimental numbers come from this project, not the papers. Tool-assisted development and writing should be disclosed in the final contribution statement.';
}
