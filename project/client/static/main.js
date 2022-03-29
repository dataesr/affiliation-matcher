const matchApi = (request) => {
    request.url = '/match_api';
    request.method = 'POST';
    $.ajax(request)
        .done(response => {
            $('#logs').html(response.logs.replace(/\n/g, '<br />'));
        })
        .fail(error => {
            console.log(error);
            $('#error').text('Erreur rencontrée et logguée dans la console.');
        });
};

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
        $('#error').text('');
        $('#logs').html('... en cours ...');
        const files = $('#fileinput').prop('files');
        const query = $('#input_query').val();
        const type = $('#input_type option:selected').val();
        const year = $('#input_year option:selected').val();
        if(query.length != 0) {
            input_json = {
                type,
                year,
                query,
                verbose: true
            }
            const request = {
                data: JSON.stringify(input_json),
                contentType: 'application/json; charset=utf-8',
                dataType: 'json'
            };
            matchApi(request);
        } else if (files.length != 0) {
            input_json = {
                type,
                year,
                verbose: false
            }
            var data = new FormData();
            data.append('file', files[0]);
            data.append('filename', files[0].name);
            data.append('type', $('#input_type option:selected').val());
            data.append('year', $('#input_year option:selected').val());
            data.append('verbose', true);
            const request = {
                data,
                processData: false,
                contentType: false,
                cache: false
            };
            matchApi(request);
        } else {
            $('#error').text('Merci de saisir une affiliation textuelle ou un fichier.');
        }
    });
});

