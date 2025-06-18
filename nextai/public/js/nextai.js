$(document).ready(function () {
    frappe.after_ajax(() => {
        if ((
                frappe.user.has_role("NextAI User") ||
                frappe.session.user === "Administrator" ||
                frappe.user.has_role("System Manager")
            ) && 
            (
                cur_frm.doc.doctype !== 'DocType' &&
                cur_frm.doc.doctype !== 'Customize Form'
            )
        ) {
            nextAIFeature();
        }
    })

});


function nextAIFeature(){
    const allowedTypes = ['Text', 'Text Editor', 'Small Text', 'Long Text', 'JSON', 'HTML Editor', 'Markdown Editor', 'Code'];

    $(document).on('click', 'input[data-fieldtype], textarea[data-fieldtype], .ace_editor, .ql-editor', function (e) {
        let $input = $(this);
        let fieldtype = $input.data('fieldtype') || $input.closest('[data-fieldtype]').data('fieldtype');

        if (!allowedTypes.includes(fieldtype)) return;

        $('.apiIcon').remove();
        $('[data-has-icon]').each(function () {
            $(this).css('padding-right', '').removeAttr('data-has-icon');
        });

        if (!$input.parent().hasClass('input-wrapper')) {
            $input.wrap('<div class="input-wrapper"></div>');
        }

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

        $container.attr('data-has-icon', true);

        const $icon = $('<button/>', {
            class: 'apiIcon',
            type: 'button',
            html: `
                <div style="
                    background: white;
                    border-radius: 9999px;
                    padding: 6px 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                ">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#333" viewBox="0 0 24 24" style="order: -1;">
                        <path d="M12 2l1.09 3.41L16 6l-2.91 0.59L12 10l-1.09-3.41L8 6l2.91-0.59L12 2zm4 14l0.77 2.3L19 20l-2.3 0.47L16 23l-0.77-2.53L13 20l2.3-0.7L16 16zm-10 0l0.77 2.3L9 20l-2.3 0.47L6 23l-0.77-2.53L3 20l2.3-0.7L6 16z"/>
                    </svg>
                    <span style="font-size: 14px; font-weight: 500; color: #333;">NextAI</span>
                </div>
            `,
            style: `
                background: linear-gradient(to right, #00f0ff, #a000ff);
                border-radius: 9999px;
                padding: 2px;
                border: none;
                cursor: pointer;
                position: absolute;
                bottom: 10px;
                right: 10px;
                z-index: 1000;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                transition: transform 0.2s ease;
            `
        }).hover(
            function() { $(this).css('transform', 'scale(1.05)'); },
            function() { $(this).css('transform', 'scale(1)'); }
        );

        if (!$container.parent().hasClass('input-wrapper')) {
            $container.wrap('<div class="input-wrapper" style="position: relative;"></div>');
        } else {
            $container.parent().css('position', 'relative');
        }

        $container.parent().append($icon);

        $icon.on('click', async function () {
            $icon.prop('disabled', true).css('opacity', 0.6).css('pointer-events', 'none');

            let keyValue = {};

            const doctype = cur_frm.doc.doctype;

            const $fieldWrapper = $container.closest('[data-fieldname]');
            const fieldname = $fieldWrapper.length ? $fieldWrapper.data('fieldname') : 'unknown';
            const fieldtype = $fieldWrapper.length ? $fieldWrapper.data('fieldtype') : 'unknown';

            if ($container.hasClass('ace_editor')) {
                const aceEditor = ace.edit($container[0]);
                keyValue = {
                    key: fieldname,
                    value: aceEditor.getValue(),
                    doctype: doctype,
                    type: fieldtype
                };

            } else if ($container.hasClass('ql-container')) {
                const $qlEditor = $container.find('.ql-editor');
                keyValue = {
                    key: fieldname,
                    value: $qlEditor.html(),
                    doctype: doctype,
                    type: fieldtype
                };

            } else {
                keyValue = {
                    key: $input.attr('id') || $input.data('fieldname') || 'unknown',
                    value: $input.val(),
                    doctype: doctype,
                    type: fieldtype
                };
            }

            try {
                const res = await makeApiCall(keyValue);

                typeText(
                    $container.hasClass('ace_editor') ? $container :
                    $container.hasClass('ql-container') ? $container :
                    $input,
                    res,
                    $container.hasClass('ace_editor') ? 'ace' :
                    $container.hasClass('ql-container') ? 'quill' : 'input',
                    () => {
                        $input.trigger('change');
                    }
                );

            } catch (err) {
                console.error("API call failed:", err);
                alert("API call failed.");
            } finally {
                setTimeout(()=>{
                    $icon.prop('disabled', false).css('opacity', 1).css('pointer-events', 'auto');
                }, 1000)
            }
        });

        if ($input.hasClass('ace_editor')) {
            const editor = ace.edit($input[0]);
            editor.focus();
        } else {
            $input.focus();
        }
    });
}


function makeApiCall(data) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'nextai.ai.get_ai_response',
            args: data,
            callback: function (r) {
                if (r.message) {
                    data = r.message
                    resolve(data.message);
                } else {
                    reject("No message in response");
                }
            },
            error: function (err) {
                reject(err);
            }
        });
    });
}


function typeText($target, text, type, callback) {
    const totalDuration = 1000;
    const startTime = performance.now();
    const len = text.length;

    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / totalDuration);
        const charsToShow = Math.floor(progress * len);
        const partial = text.slice(0, charsToShow);

        if (type === 'ace') {
            const editor = ace.edit($target[0]);
            editor.setValue(partial, -1);
        } else if (type === 'quill') {
            const $editor = $target.find('.ql-editor');
            $editor.html(partial); 
        } else {
            $target.val(partial);
        }

        if (progress < 1) {
            requestAnimationFrame(step);
        } else if (callback) {
            callback();
        }
    }

    requestAnimationFrame(step);
}
