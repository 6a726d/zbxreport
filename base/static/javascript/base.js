document.addEventListener('DOMContentLoaded', function() {
    var passwordChangeIcon = document.querySelector('.password-icon');
    passwordChangeIcon.href = "#";
    passwordChangeIcon.addEventListener('click', function(event) {
        event.preventDefault();
        var passwordChangeModal = new bootstrap.Modal(document.getElementById('passwordChangeModal'));
        passwordChangeModal.show();
    });

    document.getElementById('newPassword').addEventListener('input', function(e) {
        const password = e.target.value;
        let strength = 0;
    
        const hasLowerCase = password.match(/[a-z]/);
        const hasUpperCase = password.match(/[A-Z]/);
        const hasNumbers = password.match(/\d/);
        const hasSpecialChars = password.match(/[\W_]/);
        const hasLetters = hasLowerCase || hasUpperCase;
    
        // Define a força como 'fraca' por padrão para qualquer entrada
        if (password.length > 0) strength = 1; // Senha fraca por existir
    
        // Verifica a combinação para considerar média
        if ((hasLetters && hasNumbers) || (hasLetters && hasSpecialChars) || (hasNumbers && hasSpecialChars)) {
            strength = 2; // Média
        }
    
        // Requer todos os tipos para ser considerada forte
        if (hasLowerCase && hasUpperCase && hasNumbers && hasSpecialChars) {
            strength = 3; // Forte
        }
    
        const progressBar = document.querySelector('#passwordStrength .progress-bar');
        switch(strength) {
            case 1: // Fraca
                progressBar.style.width = "33%";
                progressBar.classList.add('bg-danger');
                progressBar.classList.remove('bg-warning', 'bg-success');
                break;
            case 2: // Média
                progressBar.style.width = "66%";
                progressBar.classList.remove('bg-danger');
                progressBar.classList.add('bg-warning');
                progressBar.classList.remove('bg-success');
                break;
            case 3: // Forte
                progressBar.style.width = "100%";
                progressBar.classList.remove('bg-danger', 'bg-warning');
                progressBar.classList.add('bg-success');
                break;
            default:
                progressBar.style.width = "0%";
                progressBar.classList.remove('bg-danger', 'bg-warning', 'bg-success');
                break;
        }
    });

    document.getElementById('filterList1').addEventListener('keyup', function() {
        filterOptions(this.value, 'list1');
    });

    document.getElementById('filterList2').addEventListener('keyup', function() {
        filterOptions(this.value, 'list2');
    });

    function filterOptions(value, listId) {
        var input = value.toLowerCase();
        var list = document.getElementById(listId);
        var options = list.options;

        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            option.style.display = option.text.toLowerCase().includes(input) ? '' : 'none';
        }
    }

    var form = document.getElementById('form1'); // Certifique-se de que este é o ID correto do seu formulário
    form.addEventListener('submit', function() {
        selectAllOptions('list2');
    });

    function selectAllOptions(listId) {
        var list = document.getElementById(listId);
        var options = list.options;
        for (var i = 0; i < options.length; i++) {
            options[i].selected = true;
        }
    }

    // Movendo itens entre as listas
    var btnToRight = document.getElementById('toRight');
    var btnToLeft = document.getElementById('toLeft');

    if (btnToRight && btnToLeft) {
        btnToRight.addEventListener('click', function() {
            moveItems(document.getElementById('list1'), document.getElementById('list2'));
        });

        btnToLeft.addEventListener('click', function() {
            moveItems(document.getElementById('list2'), document.getElementById('list1'));
        });
    }

    function moveItems(sourceList, destList) {
        Array.from(sourceList.selectedOptions).forEach(option => {
            destList.appendChild(option);
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        var reportForm = document.querySelector('#md-report form');
        
        if (reportForm) {
            reportForm.addEventListener('submit', function(event) {
                var dateFromInput = document.getElementById('date-from');
                var dateToInput = document.getElementById('date-to');
        
                // Verifica se algum dos campos está vazio
                if (!dateFromInput.value || !dateToInput.value) {
                    alert('Ambas as datas devem ser preenchidas.');
                    event.preventDefault(); // Impede a submissão do formulário
                    return;
                }
        
                // Converte os valores das datas para objetos Date
                var dateFrom = new Date(dateFromInput.value);
                var dateTo = new Date(dateToInput.value);
        
                // Verifica se a data "Até" é menor ou igual a data "De"
                if (dateTo <= dateFrom) {
                    event.preventDefault(); // Impede a submissão do formulário
                    alert('Verifique o periodo solicitado! ("De" maior que "Até")');
                }
            });
        }
    });
});

