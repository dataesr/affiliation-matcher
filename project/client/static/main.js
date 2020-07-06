// custom javascript

$( document ).ready(() => {
  console.log('Sanity Check!');
});

$('.btn').on('click', function() {
    $("#logs").html("... en cours ...");
    input_json = { 
	    type: $('#input_type option:selected').val(),
	    year: $('#input_year option:selected').val(),
	    query: $('#input_query').val(),
    }

  console.log('ttt', input_json);
  $.ajax({
    url: '/match_api',
    data: JSON.stringify(input_json),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    method: 'POST'
  })
  .done((res) => {
    console.log('new', res.logs);
    $("#logs").html(res.logs);
  })
  .fail((err) => {
    console.log(err)
  });
});

