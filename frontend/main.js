/**
 * Created by lzk on 6/4/17.
 */
function click_visible(dom){
    if (dom.className == 'visible'){
        dom.className = 'unvisible'
    }
    else {
        dom.className = 'visible'
    }
}


function GetRequest() {
    var url = location.search; //获取url中"?"符后的字串
    var theRequest = new Object();
    if (url.indexOf("?") != -1) {
        var str = url.substr(1);
        strs = str.split("&");
        for (var i = 0; i < strs.length; i++) {
            theRequest[strs[i].split("=")[0]] = decodeURIComponent(strs[i].split("=")[1]);
        }
    }
    return theRequest;
}


function read_pdf(){
    $(document).ready(function() {
        $.getJSON('img/tsconfig.json',function(json){
            var data = json;
            var tr = "";
            console.log(data);
            for(var i = 0; i < data.length; i++){
                tr += '<tr>' +
                    '<td class='+ '"' + data[i].visible +'"'+' onclick="click_visible(this)"></td>' +
                    '<td class="description">'+data[i].description+'</td>' +
                    '<td class="content"><a href='+ '"' + data[i].link +'"' + '>点击查看</a></td>' +
                    '</tr>';
            }
            console.log(tr);
            document.getElementById('table').innerHTML = tr
        });
    });
}
read_pdf();