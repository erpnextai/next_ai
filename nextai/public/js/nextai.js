$(document).ready(function () {
    const allowedTypes = ['Text', 'Text Editor', 'Small Text', 'Long Text', 'JSON', 'HTML Editor', 'Markdown Editor', 'Code'];

    $(document).on('click', 'input[data-fieldtype], textarea[data-fieldtype], .ace_editor, .ql-editor', function (e) {
        let $input = $(this);
        let fieldtype = $input.data('fieldtype') || $input.closest('[data-fieldtype]').data('fieldtype');

        if (!allowedTypes.includes(fieldtype)) return;

        // Remove any existing icons
        $('.apiIcon').remove();
        $('[data-has-icon]').each(function () {
            $(this).css('padding-right', '').removeAttr('data-has-icon');
        });

        // Wrap input if not already wrapped
        if (!$input.parent().hasClass('input-wrapper')) {
            $input.wrap('<div class="input-wrapper"></div>');
        }

        // Determine the container to attach the button to
        let $container;
        if ($input.hasClass('ace_editor')) {
            $container = $input;
        } else if ($input.closest('.ace_editor').length) {
            $container = $input.closest('.ace_editor');
        } else if ($input.hasClass('ql-editor') || $input.closest('.ql-editor').length) {
            $container = $input.closest('.ql-container');
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

        // Wrap for proper button placement
        if (!$container.parent().hasClass('input-wrapper')) {
            $container.wrap('<div class="input-wrapper" style="position: relative;"></div>');
        } else {
            $container.parent().css('position', 'relative');
        }


        $container.parent().append($icon);

        // Icon click behavior
        $icon.on('click', function () {
            let keyValue = {};

            if ($container.hasClass('ace_editor')) {
                const aceEditor = ace.edit($container[0]);
                keyValue = {
                    key: $container.closest('[data-fieldname]').data('fieldname') || 'unknown',
                    value: aceEditor.getValue()
                };
                aceEditor.setValue('New value for ' + keyValue.key, 1);
            } else if ($container.hasClass('ql-container')) {
                const $qlEditor = $container.find('.ql-editor');
                keyValue = {
                    key: $container.closest('[data-fieldname]').data('fieldname') || 'unknown',
                    value: $qlEditor.html()
                };
                $qlEditor.html('New value for ' + keyValue.key);
            } else {
                keyValue = {
                    key: $input.attr('id') || $input.data('fieldname') || 'unknown',
                    value: $input.val()
                };
                $input.val('New value for ' + keyValue.key).trigger('change');
            }

            alert(JSON.stringify(keyValue));
        });

        // Focus input/editor
        if ($input.hasClass('ace_editor')) {
            const editor = ace.edit($input[0]);
            editor.focus();
        } else {
            $input.focus();
        }
    });
});
