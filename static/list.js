$(document).ready(function() {
    $('#playlist tr')
    .filter(':has(:checkbox:checked)')
    .addClass('selected')
    .end()
    .click(function(event) {
        $(this).toggleClass('selected');
        if (event.target.type !== 'checkbox') {
            $(':checkbox', this).attr('checked',
            function() {
                return ! this.checked;
            });
        }
    });
    $('#password').blur(function() {
        $.post('/validate', {username: $('#username').val(), password: $('#password').val()}, function(data) {
          var text = ""
          if (data == "200") {
              data = "ok";
              text = "Instapaper login ok!";
          } else if (data == "403") {
              data = "authfail";
              text = "Instapaper login failed, check your username and password";
          }
          $('#result').attr("class", data);
          $('#result').html(text);
        });
    });
});

function hasClass(obj) {
    var result = false;
    if (obj.getAttributeNode("class") != null) {
        result = obj.getAttributeNode("class").value;
    }
    return result;
}

function stripe(id) {
    var even = false;
    var evenColor = arguments[1] ? arguments[1] : "#fff";
    var oddColor = arguments[2] ? arguments[2] : "#eee";

    var table = document.getElementById(id);
    if (!table) {
        return;
    }

    var tbodies = table.getElementsByTagName("tbody");
    for (var h = 0; h < tbodies.length; h++) {
        var trs = tbodies[h].getElementsByTagName("tr");
        for (var i = 0; i < trs.length; i++) {
            if (!hasClass(trs[i]) && !trs[i].style.backgroundColor) {
                var tds = trs[i].getElementsByTagName("td");
                for (var j = 0; j < tds.length; j++) {
                    var mytd = tds[j];
                    if (!hasClass(mytd) && !mytd.style.backgroundColor) {
                        mytd.style.backgroundColor = even ? evenColor: oddColor;
                    }
                }
            }
            even = !even;
        }
    }
}