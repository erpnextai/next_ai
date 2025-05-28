$(document).ready(function () {
    const allowedTypes = ['Text', 'Text Editor', 'Small Text', 'Long Text', 'Markdown Editor'];

    $(document).on('focus', 'input[data-fieldtype], textarea[data-fieldtype]', function () {
        debugger
        if (allowedTypes.includes($(this).data('fieldtype'))) {
            const $input = $(this);
            
            // Remove existing icons from all other wrappers
            $('.apiIcon').remove();
            $('input[data-has-icon], textarea[data-has-icon]').each(function () {
                const $el = $(this);
                $el.css('padding-right', '');
            });
            
            // Already wrapped? If not, wrap it and store original width
            if (!$input.parent().hasClass('input-wrapper')) {
                const inputWidth = $input.outerWidth();
                $input.wrap('<div class="input-wrapper" style="position: relative; display: inline-block;"></div>');
                $input.css('width', inputWidth + 'px');
            }
            
            // Mark as initialized
            $input.data('has-icon', true);
            
            // Add the search icon
            const $icon = $('<span/>', {
                class: 'apiIcon',
                html: '🔍',
                style: `
                position: absolute;
                top: 50%;
                right: 10px;
                transform: translateY(-50%);
                pointer-events: auto;
                cursor: pointer;
                font-size: 16px;
                color: gray;
                z-index: 10;
                `
            });
            
            $input.parent().append($icon);
            
            // Add right padding so text doesn't overlap
            const existingPaddingRight = parseInt($input.css('padding-right')) || 0;
            $input.css('padding-right', existingPaddingRight + 25 + 'px');
            
            // Optional: icon click action
            $icon.on('click', function () {
                const keyValue = {
                    id: $input.attr('id'),
                    type: $input.data('type'),
                    attributes: $input.data(),
                    value: $input.val()
                };
                const newValue = 'New value for ' + keyValue.key;
                $input.val(newValue);
                $input.trigger('change');

                alert(JSON.stringify(keyValue));
            });
        }
    });

    // Optional: hide icon on blur (if needed)
    // $(document).on('blur', 'input[type="text"], textarea', function () {
    //     $('.apiIcon').remove();
    //     $(this).css('padding-right', '');
    // });
});
