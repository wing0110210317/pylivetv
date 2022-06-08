//这个workers的js有可能会失败，因为cdn节点如果在国内，则无法转发y2b流量，如果在国外，，则y2b的视频流量不需要经过python程序，，直接由workers转发.效果更好


async function handleRequest(uurl,request) {
  var  res = await  fetch(new Request(uurl,request))
  var location  = res.headers.get("location");
  if(location != null && location != ""){
    return fetch(location);
  }else{
    return res;
  }
}

addEventListener("fetch", event => {
  let url = new URL(event.request.url);
  url.hostname = "不需要加http"; //改成你想反代的网站
  url.protocol = 'http'
  let request = new Request(url, event.request);

  const { search, pathname } = new URL(event.request.url)
  var k = "";
  if(search.startsWith("?k=")){
    k = search.replace("?k=","").replaceAll("%3D","=");
    k = atob(k);
    event.respondWith(handleRequest(k,event.request));
  }else{
    event.respondWith(
      fetch(request, {
        headers: {
          "baseUrl":"托管路由域名URL http://域名",
          'Referer': 'https://www.cloudflare.com/', //referer头,不必修改
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36' //
        }
      })
    );
  }


});
