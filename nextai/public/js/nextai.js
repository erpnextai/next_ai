$(document).ready(function () {
    const allowedTypes = ['Text', 'Text Editor', 'Small Text', 'Long Text', 'Markdown Editor', 'Code'];

    $(document).on('click', 'input[data-fieldtype], textarea[data-fieldtype], .ace_editor', function (e) {
       
            let $input = $(this);
            let fieldtype = $input.data('fieldtype') || $input.closest('[data-fieldtype]').data('fieldtype');

            if (!allowedTypes.includes(fieldtype)) return;

            // Remove any existing icons
            $('.apiIcon').remove();
            $('[data-has-icon]').each(function () {
                $(this).css('padding-right', '').removeAttr('data-has-icon');
            });

            if (!$input.parent().hasClass('input-wrapper')) {
                const inputWidth = $input.outerWidth();
                $input.wrap('<div class="input-wrapper" style="position: relative; display: inline-block;"></div>');
                $input.css('width', inputWidth + 'px');
            }

            // Get a reliable container to append icon to
            let $container;
            if ($input.hasClass('ace_editor')) {
                $container = $input;
            } else if ($input.closest('.ace_editor').length) {
                $container = $input.closest('.ace_editor');
            } else {
                $container = $input;
            }

            // Mark as initialized
            $container.attr('data-has-icon', true);

            const $icon = $('<button/>', {
                class: 'apiIcon',
                type: 'button',
                html: `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="black" viewBox="0 0 24 24">
                    <path d="M12 2l1.09 3.41L16 6l-2.91 0.59L12 10l-1.09-3.41L8 6l2.91-0.59L12 2zm4 14l0.77 2.3L19 20l-2.3 0.47L16 23l-0.77-2.53L13 20l2.3-0.7L16 16zm-10 0l0.77 2.3L9 20l-2.3 0.47L6 23l-0.77-2.53L3 20l2.3-0.7L6 16z"/>
                </svg>
                <span style="margin-left: 6px;">Next AI</span>
            `,
                style: `
                position: absolute;
                bottom: 10px;
                right: 10px;
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: 500;
                display: flex;
                align-items: center;
                cursor: pointer;
                z-index: 1000;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            `
            });


            // Wrap if needed
            if (!$container.parent().hasClass('input-wrapper')) {
                $container.wrap('<div class="input-wrapper" style="position: relative; display: inline-block;"></div>');
            }

            $container.parent().append($icon);

            // Icon click
            $icon.on('click', function () {
                let keyValue = {};
                if (fieldtype === 'Code' || fieldtype === 'Markdown Editor') {
                    // Use Ace Editor API
                    const editorElement = $container[0];
                    const aceEditor = ace.edit(editorElement);  // Assuming ACE is globally available
                    keyValue = {
                        key: $container.closest('[data-fieldname]').data('fieldname') || 'unknown',
                        value: aceEditor.getValue()
                    };

                    // Optional: write back new value
                    const newValue = 'New value for ' + keyValue.key;
                    aceEditor.setValue(newValue, 1); // 1 = cursor to start
                } else {
                    keyValue = {
                        key: $input.attr('id') || $input.data('fieldname') || 'unknown',
                        value: $input.val()
                    };
                    const newValue = 'New value for ' + keyValue.key;
                    $input.val(newValue).trigger('change');
                }

                alert(JSON.stringify(keyValue));
            });

            if ($input.hasClass('ace_editor')) {
                // Ace Editor
                var editor = ace.edit($input[0]);
                editor.focus();
            } else {
                // Regular input/textarea
                $input.focus();
            }
    });
});
