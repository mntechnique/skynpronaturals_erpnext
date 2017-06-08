function apply_restrictions(frm, le_map){    
    le_map = JSON.parse(le_map);   
    map_keys = Object.keys(le_map);
    console.log("LE Map", le_map);

    console.log("Map Keys", map_keys);

    if (map_keys) {
        for (var i=0; i<map_keys.length; i++) {
            if(frm.fields_dict[map_keys[i]].df.fieldtype == "Table"){
                $.each(le_map[map_keys[i]], function(key, value) {
                	
                    var field_name = Object.keys(value)[0];
      				
                    frm.set_query(field_name, map_keys[i], function() {
                    	console.log("TableFieldName: ", field_name, " Fieldname: ", map_keys[i], " Value: ", value[field_name]);
                        return {
                            filters: {
                              "name" : value[field_name]
                            }
                        }
                    });
                });
            } else if (frm.fields_dict[map_keys[i]].df.fieldtype == "Select") {
                frm.fields_dict[map_keys[i]].df.options = le_map[map_keys[i]].join("\n");
                refresh_field(map_keys[i]);
            } else {
                var filter_value = le_map[map_keys[i]];
                
                console.log("NormalFieldname: ", map_keys[i], " Value: ", filter_value);

                frm.set_query(map_keys[i], function() {
                	return {
                 		filters: {
                            "name" : filter_value
                        }
                 	}
                });
            }
        }
    }
}