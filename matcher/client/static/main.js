$(document).ready(() => {
    $(document).on('change', '#input_type', () => {
        type = $('#input_type option:selected').val().toLowerCase();
        switch(type) {
            case 'country': {
                $('#input_example').text('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon');
                $('#select_year').addClass('d-none');
                break;
            }
            case 'grid': {
                $('#input_example').text('Paris Dauphine University France');
                $('#select_year').addClass('d-none');
                break;
            }
            case 'rnsr': {
                $('#input_example').text('IPAG Institut de Planétologie et d\'Astrophysique de Grenoble');
                $('#select_year').removeClass('d-none');
                break;
            }
            case 'ror': {
                $('#input_example').text('Paris Dauphine University France');
                $('#select_year').addClass('d-none');
                break;
            }
            default: {
                $('#input_example').text('');
                $('#select_year').addClass('d-none');
                break;
            }
        };
    });

    $('.submit').on('click', () => {
        $('#logs').html('... en cours ...');
        input_json = {
            type: $('#input_type option:selected').val(),
            year: $('#input_year option:selected').val(),
            query: $('#input_query').val(),
            verbose: true
        }
        $.ajax({
            url: '/match_api',
            data: JSON.stringify(input_json),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            method: 'POST'
        })
        .done(result => {
            $('#logs').html(result.logs);
        })
        .fail(error => {
            console.log(error);
        });
    });
});

