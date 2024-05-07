document.addEventListener('DOMContentLoaded', function() {
    var spinnerRefresh = document.getElementById('spinner-refresh');
    var btnRefresh = document.getElementById('btn-refresh');
    btnRefresh.addEventListener('click', function() {
        btnRefresh.style.display = 'none';
        spinnerRefresh.style.display = 'block';
    });

    $('.item-dsc').on('click', function(){
        var itemId = $(this).data('id');
        $('#editModal #itemId').val(itemId);
    });
    
});
  