/**
 * Created by lzk on 6/4/17.
 */
function click(){
    var link = document.getElementsByName('link').value;
    var description = document.getElementsByName('certsName').value;
    var str = {
        "link": link,
        "description": description,
        "visible": "visible"
    };
    $.post("127.0.0.1/user/certs", str, function (result) {
        console.log(true);
    })
}
// [
//     {
//         "visible": "visible",
//         "description": "2015~2016 HUST merit student",
//         "link": "http://arxiv.org/pdf/1701.07875v2.pdf"
//     },
//     {
//         "visible": "visible",
//         "description": "2015~2016 HUST merit student",
//         "link": "https://arxiv.org/pdf/1704.00028.pdf"
//     },
//     {
//         "visible": "unvisible",
//         "description": "2015~2016 BUAA merit student",
//         "link": "https://arxiv.org/pdf/1611.01799.pdf"
//     },
//     {
//         "visible": "visible",
//         "description": "2015~2016 ZUEL merit student",
//         "link": "http://arxiv.org/pdf/1611.06624v1.pdf"
//     },
//     {
//         "visible": "visible",
//         "description": "2015~2016 HUST merit student",
//         "link": "http://arxiv.org/pdf/1612.03242v1.pdf"
//     }
// ]