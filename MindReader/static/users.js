var scroller = $('#scroller');
var template = $('#post_template');
var loaded = $('#loaded');
var sentinel = $('#sentinal');


var counter = 0;


function loadItems() {

    // Use fetch to request data and pass the counter value in the QS
    fetch(`/load?counter=${counter}`).then((response) => {

        // Convert the response data to JSON
        response.json().then((data) => {

            // If empty JSON, exit the function
            if (!data.length) {

                // Replace the spinner with "No more posts"
                sentinel.innerHTML = "No more users";
                return;
            }

            // Iterate over the items in the response
            for (var i = 0; i < data.length; i++) {

                // Clone the HTML template
                let template_clone = template.content.cloneNode(true);

                // Query & update the template content
                template_clone.title(`User - ${data[i][0]}`);
                template_clone.content(data[i][1]);

                // Append template to dom
                scroller.appendChild(template_clone);

                // Increment the counter
                counter += 1;

            }
        })
    })
}