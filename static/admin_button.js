// Make sure jQuery (django admin) is available, use admin jQuery instance

if (typeof jQuery === 'undefined') {
    var jQuery = django.jQuery;
}

var unit_information = {};

jQuery( document ).ready(function() {

    jQuery('#id_admin_unit_selected').click( function() {

        console.log('click handled');
        var phone = $( "#id_phone" ).val();
        console.log(phone);

        jQuery.ajax({
        type: "GET",
        url: '/send_code',
        dataType: 'json',
        data: {
        "phone": phone
        },
        success: function (result) {
            //TODO: output this in a modal & style
            unit_information = JSON.stringify(result);
            if (unit_information == 200){
                alert('Код подтверждения отправлен !')
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            alert("Please report this error: "+errorThrown+xhr.status+xhr.responseText);
        }
    });})

    jQuery('#id_admin_auth_code').click( function() {

        console.log('click handled');
        var phone = $( "#id_phone" ).val();
        var ver_code = $( "#id_ver_code" ).val();
        console.log(phone);

        jQuery.ajax({
        type: "GET",
        url: '/send_auth_code',
        dataType: 'json',
        data: {
        "phone": phone,
        "ver_code": ver_code,
        },
        success: function (result) {
            //TODO: output this in a modal & style
            unit_information = JSON.stringify(result);
            if (unit_information == 200){
                alert('Код подтверждения отправлен !')
            }
        },
        error: function(xhr, textStatus, errorThrown) {
            alert("Please report this error: "+errorThrown+xhr.status+xhr.responseText);
        }

});})
});