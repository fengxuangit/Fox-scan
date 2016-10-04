String.prototype.format=function(){
  if(arguments.length==0) return this;
  for(var s=this, i=0; i<arguments.length; i++)
    s=s.replace(new RegExp("\\{"+i+"\\}","g"), arguments[i]);
  return s;
};

var taskid_dict = new Array();

var init_html = "<span><button class='minimal' onclick='STOPTASK()'>STOPALL</button></span>" +
        "<span><label>All Task Number: <strong id='tasknum'>{0}</strong></label></span>"

var ChildDemo = "<p></p><table width='100%' class='insert-tab{2}'>" +
            "<tbody><tr><th width='15%'><i class='require-red'>*</i>Domain: </th>" +
            "<td><input type='text' id='' value='{0}' size='85' name='keywords' class='common-text'></td>" +
            "</tr>" +
            "<tr><th width='15%'><i class='require-red'>*</i>Operator: </th><td>" +
            "<label class='btn btn-primary btn6 mr10' >status</label>&nbsp;{3}&nbsp;" +
            "<button class='btn btn-primary btn6 mr10' onclick=\"STOPTASK('{1}')\">STOP</button>" +
            "<button class='btn btn-primary btn6 mr10' onclick=\"ShowLog('{1}')\">LOG</button>" +
            "<button class='btn btn-primary btn6 mr10 require-red' onclick=\"ShowPayload('{1}')\">Payload</button>" +
            "</td></tr></tbody></table>";

function setSelectUserNo(radioObj){
    var radioCheck= radioObj.value;
    if("True"==radioCheck){
        $(radioObj).attr("checked",false);
        $(radioObj).val("False");
    }else{
        $(radioObj).attr("checked", true);
        $(radioObj).val("True");
    }
}

function AppendChildStatus(data, $obj){
    var child = ChildDemo.concat();
    //当返回的任务数大于现在的数据时候才改变.
    $('#tasknum').html(data['number']);
    if (taskid_dict.indexOf(data['taskid']) == -1)
        taskid_dict.push(data['taskid']);
    $obj.empty();
    var targetlist = [];
    $.each(data['data'], function(n, value){
        targetlist.push(value);
    });
    targetlist.sort(function (a, b) {
        if(a.success > b.success){
            return -1;
        }else if (a.success > b.success){
            return 0;
        }else{
            return 1;
        }
    });
    var str = "";
    for (var i=0;i< targetlist.length; i++){
//        $obj.append()
        var value = targetlist[i];
        if (value['success'] == 1){
            str = child.format(value['target'], value['taskid'], " red_table", value['status']);
        }else{
            str = child.format(value['target'], value['taskid'], "", value['status']);
        }
        $obj.append(str);
    }
}


function ajaxGetjson($obj){
    $.ajax({
        url  : '/action/showtask?action=refresh',
        dataType : "json",
        success : function (jdata) {
            AppendChildStatus(jdata, $obj);
        }
    });
}

function STOPTASK(taskid="") {
    if (taskid == ""){
        for (var i =0;i<taskid_dict.length;i++){
            taskid += taskid_dict[i] + ",";
        }
    }
    $.ajax({
        url  : '/action/stoptask?taskidlist=' + taskid,
        dataType : "json",
        success : function (jdata) {
        }
    });
}

function ModeChange(obj) {
    num = obj.value;
    if (num == 0){
        $('.passive').hide();
    }else if(num == 1){
        $('.passive').show();
    }
    $(obj).attr("checked",true);
    $(obj).closest('radio').attr("checked", false);
}


function getRootDomain(domain){
    var repartten = /http[s]{0,1}:\/\/(.*?)\//i;
    return domain.match(repartten)
}
