#-*- coding: utf-8 -*-

class FormOptions:   
    
 
    def __init__(self, method='post', action='.', enctype=None, css_class=None,
                id=None, submit_label='Submit', include_help_text=True,
                base_error_msg='Error:', images_links=None, css_p_map={}):
        
        if not action:
            raise ValueError('You must define form action')

        (self.method, self.action, self.enctype, self.css_class, self.id,
         self.submit_label, self.include_help_text, self.base_error_msg, 
         self.images_links, self.css_p_map) = (method, action, enctype, css_class, id, submit_label,
                            include_help_text, base_error_msg, images_links, css_p_map)       
         
