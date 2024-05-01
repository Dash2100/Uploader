$(document).ready(function () {
    focusFirstInput();

    // keypad number
    $('.key').not('.backspace, .clear').click(function () {
        var inputVal = $(this).text();

        $('.pincode').each(function () {
            if ($(this).val() == '') {
                $(this).val(inputVal);
                return false;
            }
        });

        //vibrate
        if (navigator.vibrate) {
            navigator.vibrate(1);
        }
    });

    $('.backspace').click(function () {
        var filled = $('.pincode').filter(function () {
            return $(this).val() != '';
        });

        if (filled.length > 0) {
            filled.last().val('');
        }

        //vibrate
        if (navigator.vibrate) {
            navigator.vibrate(1);
        }
    });

    $('.clear').click(function () {
        $('.pincode').val('');

        //vibrate
        if (navigator.vibrate) {
            navigator.vibrate(1);
        }
    });

    // focus next input
    $('.pincode').on('input', function () {
        //check if input is number
        let num = /^\d+$/.test($(this).val());

        if (num) {
            $(this).next().focus();
        } else {
            $(this).val('');
        }
    });

    // focus previous input
    $('.pincode').on('keydown', function (e) {
        if (e.keyCode == 8) {
            if ($(this).val() == '') {
                $(this).prev().focus();
            }
        }
    });

    $('.keypad, .pincode-area').on('click input', function () {
        let pin = '';

        $('.pincode').each(function () {
            pin += $(this).val();
        });

        //check if pin is complete
        if (pin.length === 6) {
            $('.pincode').blur();
            console.log(pin);

            $('.pincode').val('');

            if (pin === '123456') {
                passed();
            } else {
                failed();
            }
        }
    });

    //allow paste action on pin input
    $('.pincode').on('paste', function (e) {
        e.preventDefault();

        var paste = (e.originalEvent || e).clipboardData.getData('text/plain');
        var pasteArray = paste.split('');

        $('.pincode').each(function (index) {
            if (pasteArray[index]) {
                $(this).val(pasteArray[index]);
            }
        });
    });

});

function focusFirstInput() {
    if ($(window).width() > 700) {
        $('.pincode').first().focus();
    }
}


//ui
function passed(){
    $('.input-area').addClass('fade-out')

    $('.download-area').show()
    $('.download-area').addClass('download-area--show')
}

function failed(){
    $('.pincode-area').addClass('shake');
    setTimeout(function () {
        $('.pincode-area').removeClass('shake');
    }, 300);

    focusFirstInput();

    //vibrate
    if (navigator.vibrate) {
        navigator.vibrate(100);
    }
}