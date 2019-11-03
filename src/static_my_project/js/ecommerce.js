$(document).ready(function () {

    //contact-form handler
    var contactForm = $(".contact-form");
    var contactFormMethod = contactForm.attr("method");
    var contactFormEndpoint = contactForm.attr("action");

    function displaySubmit(submitBtn, defaultText, doSubmit) {
        if (doSubmit) {
            submitBtn.addClass("disabled");
            submitBtn.html("<i class='fa fa-spin fa-spinner'></i> Hold On... ");
        } else {
            submitBtn.removeClass("disabled");
            submitBtn.html(defaultText);
        }
    }

    contactForm.submit(function (event) {
        event.preventDefault();

        var contactFormSubmitBtn = contactForm.find("[type=submit]");
        var contactFormSubmitBtnTxt = contactFormSubmitBtn.text();

        var contactFormData = contactForm.serialize();
        displaySubmit(contactFormSubmitBtn, "", true);
        $.ajax({
            method: contactFormMethod,
            url: contactFormEndpoint,
            data: contactFormData,
            success: function (data) {
                contactForm[0].reset();
                $.alert({
                    title: "Success!",
                    content: data.message,
                    theme: "modern"
                });
                setTimeout(function () {
                    displaySubmit(contactFormSubmitBtn, contactFormSubmitBtnTxt, false);
                }, 500);
            },
            error: function (err) {
                console.log(err);
                var jsonData = err.responseJSON;
                var msg = "";

                $.each(jsonData, function (key, value) {
                    msg += key + ": " + value[0].message + "<br/>";
                });

                $.alert({
                    title: "OOPS!",
                    content: msg,
                    theme: "modern"
                });
                setTimeout(function () {
                    displaySubmit(contactFormSubmitBtn, contactFormSubmitBtnTxt, false);
                }, 500);
            }
        });
    })


    // auto-search
    var searchForm = $(".search-form");
    var searchInput = searchForm.find("[name='q']");  // <input name='q' ...>
    var typingTimer;
    var typingInterval = 500;  // 0.5 seconds

    var searchBtn = searchForm.find("[type=submit]");  // finds the submit button

    searchInput.keyup(function (event) {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(performSearch, typingInterval);
    });

    searchInput.keydown(function (event) {
        clearTimeout(typingTimer);
    });

    function displaySearching() {
        searchBtn.addClass("disabled");
        searchBtn.html("<i class='fa fa-spin fa-spinner'></i> Searching... ");
    }

    function performSearch() {
        displaySearching();
        var query = searchInput.val();
        setTimeout(function () {
            window.location.href = '/search/?q=' + query;
        }, 1000);
    }


    // Cart & Product events
    var productForm = $(".form-product-ajax");

    productForm.submit(function (event) {
        event.preventDefault();

        var thisForm = $(this)

        var actionEndpoint = thisForm.attr("action");
        var httpMethod = thisForm.attr("method");
        var formData = thisForm.serialize();

        $.ajax({
            url: actionEndpoint,
            method: httpMethod,
            data: formData,
            success: function (data) {
                console.log("SUCCESS: " + data);
                var submitSpan = thisForm.find(".submit-span");
                if (data.added) {
                    submitSpan.html("In Cart <button class='btn btn-link' type='submit'>remove?</button>")
                } else {
                    submitSpan.html("<button class='btn btn-success' type='submit'>Add to Cart</button>")
                }

                var navbarCount = $(".navbar-cart-count");
                navbarCount.text(data.cartItemCount);

                var currentPath = window.location.href;
                if (currentPath.indexOf("cart") != -1) {
                    refreshCart();
                }

            },
            error: function (err) {
                console.log(err);
                $.alert({
                    title: "OOPS!",
                    content: " An error occurred, try again.",
                    theme: "modern"
                })
            }
        })

        function refreshCart() {
            console.log("in current cart");
            var cartTable = $(".cart-table");
            var cartBody = cartTable.find(".cart-body");
            var productRows = cartBody.find(".cart-product");

            var currentURL = window.location.href;

            var refreshCartURL = '/api/cart/';
            var refreshCartMethod = "GET";
            var data = {};

            $.ajax({
                url: refreshCartURL,
                method: refreshCartMethod,
                data: data,
                success: function (data) {
                    var hiddenCartItemRemoveForm = $(".cart-remove-form");

                    if (data.products.length > 0) {
                        data.products = data.products.splice(0).reverse();
                        productRows.html("");
                        var i = data.products.length;
                        $.each(data.products, function (index, value) {
                            var newCartItemRemove = hiddenCartItemRemoveForm.clone();
                            newCartItemRemove.css("display", "block");
                            newCartItemRemove.find(".cart-product-id").val(value.id);

                            cartBody.prepend("<tr><th scope=\"row\">"
                                + i
                                + "</th><td><a href='" + value.url + "'>"
                                + value.title
                                + "</a>"
                                + newCartItemRemove.html()
                                + "</td><td>"
                                + value.price
                                + "</td></tr>");
                            --i;
                        });
                        cartBody.find(".cart-subtotal").text(data.sub_total);
                        cartBody.find(".cart-total").text(data.total);
                    } else {
                        cartTable.html("<p class='lead'>Empty!</p>");
                    }
                },
                error: function (err) {
                    console.log(err);
                    $.alert({
                        title: "OOPS!",
                        content: " An error occurred, try again.",
                        theme: "modern"
                    });

                    window.location.href = currentURL;
                }
            });
        }

    })
});