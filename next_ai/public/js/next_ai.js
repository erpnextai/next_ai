frappe.provide("nextai.cache");

$(document).ready(function () {
    setTimeout(()=>{
        if (
            (
                frappe.user.has_role("NextAI User") ||
                frappe.session.user === "Administrator" ||
                frappe.user.has_role("System Manager")
            ) && 
            (
                !cur_frm || !cur_frm.doc ||  
                (
                    cur_frm.doc.doctype !== 'DocType' &&
                    cur_frm.doc.doctype !== 'Customize Form'
                )
            )
        ) {
            nextAIFeature();
        }
    }, 2000)
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
                    padding: 3px 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                ">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="14" fill="currentColor" class="bi bi-stars" viewBox="0 0 16 16">
                        <path d="M7.657 6.247c.11-.33.576-.33.686 0l.645 1.937a2.89 2.89 0 0 0 1.829 1.828l1.936.645c.33.11.33.576 0 .686l-1.937.645a2.89 2.89 0 0 0-1.828 1.829l-.645 1.936a.361.361 0 0 1-.686 0l-.645-1.937a2.89 2.89 0 0 0-1.828-1.828l-1.937-.645a.361.361 0 0 1 0-.686l1.937-.645a2.89 2.89 0 0 0 1.828-1.828zM3.794 1.148a.217.217 0 0 1 .412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 0 1 0 .412l-1.162.387A1.73 1.73 0 0 0 4.593 5.69l-.387 1.162a.217.217 0 0 1-.412 0L3.407 5.69A1.73 1.73 0 0 0 2.31 4.593l-1.162-.387a.217.217 0 0 1 0-.412l1.162-.387A1.73 1.73 0 0 0 3.407 2.31zM10.863.099a.145.145 0 0 1 .274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 0 1 0 .274l-.774.258a1.16 1.16 0 0 0-.732.732l-.258.774a.145.145 0 0 1-.274 0l-.258-.774a1.16 1.16 0 0 0-.732-.732L9.1 2.137a.145.145 0 0 1 0-.274l.774-.258c.346-.115.617-.386.732-.732z"/>
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
            let keyValue = {};
            let doctype = '';
            if (cur_frm){
                doctype = cur_frm.doc.doctype;
            }else if(cur_dialog){
                doctype = cur_dialog.doc.doctype;
            }

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

            cloned = structuredClone(keyValue)
            delete cloned['value']
            req = JSON.stringify(cloned)

            if ((nextai.cache[req] != undefined) && (nextai.cache[req] == keyValue['value'])){
                frappe.msgprint('⚠️ Invalid Input: Cannot process AI-generated output as a new prompt. Please enter your own input.')
            } else {
                nextai.cache = {};
                try {
                    const res = await makeApiCall(keyValue);

                    $icon.prop('disabled', true).css('opacity', 0.6).css('pointer-events', 'none');
                    
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
                    // alert("API call failed.");
                } finally {
                    setTimeout(()=>{
                        $icon.prop('disabled', false).css('opacity', 1).css('pointer-events', 'auto');
                    }, 1000)
                }
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
            method: 'next_ai.ai.get_ai_response',
            args: data,
            freeze:true, freeze_message:__("Connecting with NextAI"),
            callback: function (r) {
                if (r.message) {
                    const responseData = r.message.message;

                    delete data['value']
                    const cacheKey = JSON.stringify(data);
                    nextai.cache[cacheKey] = responseData;
                    
                    resolve(responseData);
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
