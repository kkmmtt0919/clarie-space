const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = __dirname;
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.mp4':'video/mp4','.mp3':'audio/mpeg'};
const port = Number(process.env.PORT || 4193);
http.createServer((req,res) => {
  let name;
  try { name = decodeURIComponent(new URL(req.url,'http://localhost').pathname); } catch { res.writeHead(400);res.end();return; }
  if (name === '/') name='/index.html';
  const file = path.resolve(root,'.'+name);
  const relative=path.relative(root,file);
  if(relative.startsWith('..')||path.isAbsolute(relative)||relative.split(path.sep).some(p=>p.startsWith('.'))||relative.startsWith('node_modules')) {res.writeHead(403);res.end();return;}
  fs.stat(file,(error,stat)=>{
    if(error || !stat.isFile()){res.writeHead(404);res.end('Not found');return;}
    const headers={'Content-Type':mime[path.extname(file).toLowerCase()]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Content-Length':stat.size};
    if(path.extname(file).toLowerCase()==='.mp3'){
      headers['Accept-Ranges']='bytes';
      if(req.headers.range){
        const range=/^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
        const start=range?(range[1]?Number(range[1]):Math.max(0,stat.size-Number(range[2]))):NaN;
        const end=range?(range[1]&&range[2]?Math.min(Number(range[2]),stat.size-1):stat.size-1):NaN;
        if(!range||(!range[1]&&!range[2])||!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||start>=stat.size){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`});res.end();return;}
        res.writeHead(206,{...headers,'Content-Length':end-start+1,'Content-Range':`bytes ${start}-${end}/${stat.size}`});
        fs.createReadStream(file,{start,end}).pipe(res);return;
      }
    }
    res.writeHead(200,headers);
    fs.createReadStream(file).pipe(res);
  });
}).listen(port,'127.0.0.1',()=>console.log(`Claire: http://127.0.0.1:${port}`));
