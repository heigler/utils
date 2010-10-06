$(function(){

	form_validation = function(url){
		var form = $('form');
		var submit_button = $('input[type=submit]', form)
		var ajax_url = url
		
		$('label').each(function(){
			$(this).append('<span class="ajax_msg"></span>');
		});
		
		
		var call_ajax = function(field_name, field_value){
			$.ajax({
				type: 'POST',
				url: ajax_url,
				dataType: 'json',
				data: {'field_name': field_name, 'field_value': field_value},
				success: function(data){
					var span_msg = $('label[for=id_'+field_name+'] span.ajax_msg');
					span_msg.text(data['field_message']);
					if(data['status'] == 'valid'){
						submit_button.removeAttr('disabled');
						span_msg.attr('class', 'ajax_msg ok');
					}else{
						submit_button.attr('disabled', 'disabled');
						span_msg.attr('class', 'ajax_msg');
					}
				}
			});
			
		}
		
		
		$('label').bind('keyup keydown click', function(){
			var self = $(this);
			var field_name = $('input,select', self).attr('name');
			var field_value = $('input,select', self).val();
			call_ajax(field_name, field_value);
		});
		
		
	}

});
