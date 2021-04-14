$('.submit').on('click', function() {
    $('#logs').html('... en cours ...');
    input_json = { 
	    type: $('#input_type option:selected').val(),
	    year: $('#input_year option:selected').val(),
	    query: $('#input_query').val(),
    }
    $.ajax({
        url: '/match_api',
        data: JSON.stringify(input_json),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        method: 'POST'
    })
    .done(res => {
        $('#logs').html(res.logs);
    })
    .fail(err => {
        console.log(err)
    });
});

