import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.cwd();
const projects = [[".", "35-desaccord-obligations", "Désaccord des modèles", "Désaccord pénalisé", "Prévision moyenne"]];
const output = path.join(process.env.TMPDIR || '/tmp', '35-desaccord-obligations-previews');
await fs.mkdir(output, {recursive: true});

for (const [folder, slug, title, model, benchmark] of projects) {
  const repo = path.join(root, folder);
  const data = JSON.parse(await fs.readFile(path.join(repo, 'results/tables/workbook_source.json'), 'utf8'));
  const wb = Workbook.create();
  const summary = wb.worksheets.add('Comparaison');
  const monthly = wb.worksheets.add('Rendements');
  const extra = data.scored_returns === 'excess';
  const scoreColumns = extra ? ['H', 'I'] : ['B', 'C'];
  const last = data.dates.length + 7;
  for (const sheet of [summary, monthly]) {
    sheet.showGridLines = false;
    sheet.getRange('A1:I25').format.font = {name:'Arial', size:11, color:'#233445'};
    sheet.getRange('A1:I25').format.verticalAlignment = 'center';
  }
  summary.tabColor = '#17659A';
  summary.getRange('A:A').format.columnWidth = 43;
  summary.getRange('B:C').format.columnWidth = 29;
  summary.getRange('A2').values = [[title]];
  summary.getRange('A2').format.font = {name:'Arial', size:16, bold:true};
  summary.getRange('A3:C3').format.borders = {bottom:{style:'thin',color:'#17659A'}};
  summary.getRange('A4').values = [[`${data.dates[0]} au ${data.dates.at(-1)}. Frais de ${data.cost_bps} points de base.`]];
  summary.getRange('A6:C7').values = [['Mesure', 'Modèle étudié', 'Repère'], ['', model, benchmark]];
  summary.getRange('A6:C6').format = {fill:'#17659A',font:{name:'Arial',bold:true,color:'#FFFFFF'},horizontalAlignment:'center'};
  summary.getRange('A7:C7').format.wrapText = true;
  summary.getRange('A7:C7').format.rowHeight = 32;
  const labels = {8:'Rendement annuel composé',9:'Risque annuel',10:'Rotation annuelle du capital',12:'Rendement moyen mensuel',13:'Variance mensuelle',14:'Pénalité annuelle de risque',15:'Équivalent certain annuel',17:'Écart du modèle au repère',18:'Points de pourcentage par an',20:'Aversion au risque',21:'Mois par année',22:'Nombre de mois observés'};
  for (const [row,label] of Object.entries(labels)) summary.getRange(`A${row}`).values = [[label]];
  summary.getRange('B20:B21').values = [[data.gamma],[12]];
  summary.getRange('B20').format.fill = '#FFF0CB';
  summary.getRange('B20').dataValidation = {rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
  summary.getRange('B22').formulas = [[`=COUNT('Rendements'!A8:A${last})`]];
  summary.getRange('B17').formulas = [['=100*(B15-C15)']];
  summary.getRange('B17').setNumberFormat('0.00');
  summary.getRange('A24').values = [['Modifier B20 change la pénalité de risque et les équivalents certains.']];
  summary.getRange('A25').values = [[extra ? 'Le risque et l’équivalent certain utilisent les rendements moins le taux sans risque.' : 'Le risque et l’équivalent certain utilisent les rendements totaux nets.']];
  for (let j=0;j<2;j++) {
    const c = ['B','C'][j], netCol=['B','C'][j], wealthCol=['F','G'][j], turnoverCol=['D','E'][j], score=scoreColumns[j];
    const formulas={8:`=('Rendements'!${wealthCol}${last}/100)^(B$21/B$22)-1`,9:`=STDEV.S('Rendements'!${score}8:${score}${last})*SQRT($B$21)`,10:`=AVERAGE('Rendements'!${turnoverCol}8:${turnoverCol}${last})*$B$21`,12:`=AVERAGE('Rendements'!${score}8:${score}${last})`,13:`=VAR.S('Rendements'!${score}8:${score}${last})`,14:`=0.5*$B$20*$B$21*${c}13`,15:`=$B$21*${c}12-${c}14`};
    for(const [r,f] of Object.entries(formulas)) summary.getRange(`${c}${r}`).formulas=[[f]];
  }
  summary.getRange('B8:C15').setNumberFormat('0.00%');
  summary.getRange('B10:C10').setNumberFormat('0.00');
  summary.getRange('B13:C13').setNumberFormat('0.000000');
  summary.getRange('A15:C15').format.fill = '#EDF3F7';
  summary.getRange('A8:C22').format.rowHeight = 23;
  monthly.getRange('A:A').format.columnWidth = 14;
  monthly.getRange('B:I').format.columnWidth = 22;
  monthly.getRange('A2').values = [['Rendements mensuels du test principal']];
  monthly.getRange('A2').format.font = {name:'Arial',size:16,bold:true};
  monthly.getRange('A3').values = [[`Source ${'https://github.com/Guilou001/'+slug+'/blob/main/results/tables/paths.parquet'}`]];
  monthly.getRange('A4').values = [[`Modèle ${model}. Repère ${benchmark}. Rendements nets des frais.`]];
  monthly.getRange('A5').values = [['Indices de richesse calculés depuis 100 juste avant le premier mois.']];
  const headers=['Fin du mois','Rendement modèle','Rendement repère','Rotation modèle','Rotation repère','Indice modèle','Indice repère'];
  if(extra) headers.push('Excédent modèle','Excédent repère');
  monthly.getRangeByIndexes(6,0,1,headers.length).values=[headers];
  const header=monthly.getRangeByIndexes(6,0,1,headers.length);
  header.format={fill:'#17659A',font:{name:'Arial',color:'#FFFFFF',bold:true},horizontalAlignment:'center'};
  const rows = data.dates.map((d,i)=>[new Date(d+'T00:00:00Z'),data.series[0].net[i],data.series[1].net[i],data.series[0].turnover[i],data.series[1].turnover[i]]);
  monthly.getRange(`A8:E${last}`).values=rows;
  monthly.getRange(`A8:A${last}`).setNumberFormat('yyyy-mm-dd');
  monthly.getRange(`B8:C${last}`).setNumberFormat('0.00%');
  monthly.getRange(`D8:G${last}`).setNumberFormat('0.00');
  monthly.getRange('F8:G8').formulas=[['=100*(1+B8)','=100*(1+C8)']];
  monthly.getRange('F9:G9').formulas=[['=F8*(1+B9)','=G8*(1+C9)']];
  monthly.getRange(`F9:G${last}`).fillDown();
  if(extra){
    monthly.getRange(`H8:I${last}`).values=data.dates.map((_,i)=>data.series.map(s=>s.scored_returns[i]));
    monthly.getRange(`H8:I${last}`).setNumberFormat('0.00%');
  }
  monthly.freezePanes.freezeRows(7);
  wb.recalculate();
  for(let j=0;j<2;j++) assert.ok(Math.abs(summary.getRange(`${['B','C'][j]}15`).values[0][0]-data.series[j].ce)<1e-10);
  const old=summary.getRange('B15').values[0][0];
  summary.getRange('B20').values=[[0]];
  wb.recalculate();
  assert.ok(Math.abs(summary.getRange('B15').values[0][0]-12*summary.getRange('B12').values[0][0])<1e-12);
  assert.ok(summary.getRange('B15').values[0][0]>old);
  summary.getRange('B20').values=[[data.gamma]];
  wb.recalculate();
  console.log(slug, (await wb.inspect({kind:'table',range:'Comparaison!A12:C17',include:'values,formulas',tableMaxRows:6,tableMaxCols:3,maxChars:1700})).ndjson);
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:2000});
  console.log(errors.ndjson);
  for(const [sheet,range] of [['Comparaison','A1:C25'],['Rendements',extra?'A1:I16':'A1:G16']]){
    const preview=await wb.render({sheetName:sheet,range,scale:1.5,format:'png'});
    await fs.writeFile(path.join(output,`${slug}-${sheet}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  const file=await SpreadsheetFile.exportXlsx(wb);
  await fs.mkdir(path.join(repo,'reports'),{recursive:true});
  await file.save(path.join(repo,'reports/controle.xlsx'));
  await fs.writeFile(path.join(repo,'reports/verification_classeur.json'), JSON.stringify({engine:'@oai/artifact-tool',delta_ce:summary.getRange('B17').values[0][0]/100,months:data.dates.length,ce:summary.getRange('B15:C15').values[0],risk_aversion_change_verified:true,native_excel_opened:false},null,2)+'\n');
}
