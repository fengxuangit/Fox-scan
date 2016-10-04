function ShowDiv(show_div, bg_div) {
    document.getElementById(show_div).style.display = 'block';
    document.getElementById(bg_div).style.display = 'block';
    var bgdiv = document.getElementById(bg_div);
    bgdiv.style.width = document.body.scrollWidth;
    // bgdiv.style.height = $(document).height();
    $("#" + bg_div).height($(document).height());
};
//关闭弹出层
function CloseDiv(show_div, bg_div) {
    document.getElementById(show_div).style.display = 'none';
    document.getElementById(bg_div).style.display = 'none';
};

function ShowLog(taskid){
    $.ajax({
        url  : '/action/showtask?type=log&taskid=' + taskid,
        dataType : "json",
        timeout: 10000,
        error  : function(XMLHttpRequest, textStatus, errorThrown){
            ShowLogDetail("Nothing here");
        },
        success : function (data) {
            ShowLogDetail(data);
        }
    });
}
var close_html = "<div style='text-align: right; cursor: default; height: 40px;'><br />" +
    "<span style='font-size: 16px;' onclick=\"CloseDiv('hides','shows')\">关闭</span></div>";

function ShowLogDetail(data) {
    $('#hides').empty();
    $('#hides').append(close_html);
    var html = "";
    $.each(data['log'], function(n, value){
        for (var key in value){
            html += "<B>" + key + "</B>" + ":  " + value[key] + "  ";
        }
        html += "<br/>\n";
       $('#hides').append(html);
    });
    ShowDiv('hides','shows');

}

function showdatadetail(data){
    $('#hides').empty();
    $('#hides').append(close_html);
    var html = "";
    if (data['data'] == []){
        return;
    }
//    alert();
    $.each(data['data'][0]['value'][0]['data'], function(n, value){
        for (var key in value){
            html += "<B>" + key + "</B> " + ":  " + value[key] + "  ";
        }
        html += "<br/>\n";
       $('#hides').append(html);
    });
    ShowDiv('hides','shows');
}


function ShowPayload(taskid) {
    $.ajax({
        url  : '/action/showtask?type=payload&taskid=' + taskid,
        dataType : "json",
        timeout: 10000,
        error  : function(XMLHttpRequest, textStatus, errorThrown){
            ShowLogDetail("Nothing here");
        },
        success : function (data) {
            showdatadetail(data);
        }
    });
}
