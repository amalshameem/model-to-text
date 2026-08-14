import json
import xml.etree.ElementTree as ET
from collections import defaultdict, deque

def remove_namespaces(element):
    """Recursively remove namespaces from element tags."""
    for el in element.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]
    return element

def parse_bpmn(root):
    parsed_json = {
        "Process Name": "Unknown Process",
        "Actors": [],
        "Start Events": [],
        "End Events": [],
        "Sequence": []
    }
    
    # Process Name
    process = root.find('.//process')
    if process is not None and process.get('name'):
        parsed_json["Process Name"] = process.get('name')
    elif root.find('.//collaboration') is not None and root.find('.//collaboration').get('name'):
        parsed_json["Process Name"] = root.find('.//collaboration').get('name')
        
    # Extract Pools (Participants)
    pool_map = {} # process_id -> participant_name
    for participant in root.findall('.//participant'):
        name = participant.get('name')
        proc_ref = participant.get('processRef')
        if name and proc_ref:
            pool_map[proc_ref] = name.strip()
            
    # Extract Roles (Lanes) & Map to Pools
    lane_map = {} # node_id -> [pool_name, lane_name] or just lane_name
    actors = set()
    
    for pool_name in pool_map.values():
        if pool_name:
            actors.add(pool_name)
            
    for proc in root.findall('.//process'):
        p_id = proc.get('id')
        pool_name = pool_map.get(p_id)
        
        # All children of this process belong to this pool
        if pool_name:
            for child in proc.iter():
                child_id = child.get('id')
                if child_id:
                    lane_map[child_id] = f"Pool: {pool_name}"
                    
        # Override or append lane info
        for lane in proc.findall('.//lane'):
            lane_name = lane.get('name', 'Unknown Role').strip()
            if lane_name and lane_name != 'Unknown Role':
                actors.add(lane_name)
                
            for flowNodeRef in lane.findall('.//flowNodeRef'):
                if flowNodeRef.text:
                    node_id = flowNodeRef.text.strip()
                    if node_id in lane_map and lane_map[node_id].startswith("Pool:"):
                        lane_map[node_id] = f"{lane_map[node_id]} | Lane: {lane_name}"
                    else:
                        lane_map[node_id] = f"Lane: {lane_name}"
                        
    parsed_json["Actors"] = list(actors)
                
    # Extract Data Objects/Stores/Inputs/Outputs & Annotations
    data_objects = {}
    for do in root.findall('.//dataObjectReference'):
        data_objects[do.get('id')] = do.get('name', 'Data Object').strip()
    for ds in root.findall('.//dataStoreReference'):
        data_objects[ds.get('id')] = ds.get('name', 'Data Store').strip()
    for di in root.findall('.//dataInput'):
        if di.get('name'):
            data_objects[di.get('id')] = di.get('name').strip()
    for do_out in root.findall('.//dataOutput'):
        if do_out.get('name'):
            data_objects[do_out.get('id')] = do_out.get('name').strip()
    for do_base in root.findall('.//dataObject'):
        if do_base.get('name') and do_base.get('id'):
            data_objects[do_base.get('id')] = do_base.get('name').strip()
    for ds_base in root.findall('.//dataStore'):
        if ds_base.get('name') and ds_base.get('id'):
            data_objects[ds_base.get('id')] = ds_base.get('name').strip()
        
    annotations = {}
    for text in root.findall('.//textAnnotation'):
        t_el = text.find('.//text')
        if t_el is not None and t_el.text:
            annotations[text.get('id')] = t_el.text.strip()
            
    # Associate Annotations
    node_annotations = defaultdict(list)
    for assoc in root.findall('.//association'):
        source = assoc.get('sourceRef')
        target = assoc.get('targetRef')
        if source in annotations:
            node_annotations[target].append(annotations[source])
        if target in annotations:
            node_annotations[source].append(annotations[target])

    # Nodes
    nodes = {}
    node_types = ['startEvent', 'endEvent', 'task', 'userTask', 'serviceTask', 
                  'scriptTask', 'sendTask', 'receiveTask', 'exclusiveGateway', 
                  'parallelGateway', 'inclusiveGateway', 'complexGateway', 
                  'eventBasedGateway', 'businessRuleTask', 'manualTask',
                  'intermediateCatchEvent', 'intermediateThrowEvent', 'callActivity',
                  'boundaryEvent', 'subProcess', 'adHocSubProcess', 'transaction']
                  
    start_events = []

    for n_type in node_types:
        for el in root.findall(f'.//{n_type}'):
            node_id = el.get('id')
            name = el.get('name', '').strip()
            
            if 'Gateway' in n_type or 'gateway' in n_type.lower():
                desc = f"Gateway ({name})" if name else "Gateway"
            elif 'Event' in n_type or 'event' in n_type.lower():
                event_type_str = n_type
                if el.find('.//timerEventDefinition') is not None:
                    event_type_str = f"Timer {n_type}"
                elif el.find('.//messageEventDefinition') is not None:
                    event_type_str = f"Message {n_type}"
                elif el.find('.//errorEventDefinition') is not None:
                    event_type_str = f"Error {n_type}"
                elif el.find('.//signalEventDefinition') is not None:
                    event_type_str = f"Signal {n_type}"
                elif el.find('.//conditionalEventDefinition') is not None:
                    event_type_str = f"Conditional {n_type}"
                elif el.find('.//escalationEventDefinition') is not None:
                    event_type_str = f"Escalation {n_type}"
                elif el.find('.//cancelEventDefinition') is not None:
                    event_type_str = f"Cancel {n_type}"
                elif el.find('.//compensateEventDefinition') is not None:
                    event_type_str = f"Compensate {n_type}"
                elif el.find('.//terminateEventDefinition') is not None:
                    event_type_str = f"Terminate {n_type}"
                
                desc = f"Event ({name}) [{event_type_str}]" if name else f"Event [{event_type_str}]"
            else:
                desc = f"Task ({name})" if name else "Task"
                if el.find('.//standardLoopCharacteristics') is not None:
                    desc += " [Loop]"
                if el.find('.//multiInstanceLoopCharacteristics') is not None:
                    desc += " [Multi-Instance]"
                
            # Add Lane/Pool info
            if node_id in lane_map:
                desc += f" [{lane_map[node_id]}]"
                
            # Add Annotations
            if node_id in node_annotations:
                desc += f" [Note: {' | '.join(node_annotations[node_id])}]"
                
            # Add Data Object associations (input/output)
            inputs = []
            outputs = []
            for d_in in el.findall('.//dataInputAssociation'):
                src = d_in.find('.//sourceRef')
                if src is not None and src.text in data_objects:
                    inputs.append(data_objects[src.text])
            for d_out in el.findall('.//dataOutputAssociation'):
                tgt = d_out.find('.//targetRef')
                if tgt is not None and tgt.text in data_objects:
                    outputs.append(data_objects[tgt.text])
                    
            if inputs or outputs:
                data_desc = []
                if inputs: data_desc.append(f"Reads: {', '.join(inputs)}")
                if outputs: data_desc.append(f"Writes: {', '.join(outputs)}")
                desc += f" [{'; '.join(data_desc)}]"
                
            nodes[node_id] = desc
            
            if n_type == 'startEvent':
                start_events.append(node_id)
                start_name = name if name else "Start Event"
                parsed_json["Start Events"].append(f"{start_name} [{event_type_str}]")
            elif n_type == 'endEvent':
                end_name = name if name else "End Event"
                parsed_json["End Events"].append(f"{end_name} [{event_type_str}]")
                
    # Build adjacency list (Sequence Flows and Message Flows)
    adj = defaultdict(list)
    flows_list = []
    
    for flow in root.findall('.//sequenceFlow'):
        flows_list.append(flow)
    for flow in root.findall('.//messageFlow'):
        flows_list.append(flow)
        
    for flow in flows_list:
        source = flow.get('sourceRef')
        target = flow.get('targetRef')
        name = flow.get('name', '').strip()
        adj[source].append((target, name, flow.tag)) 
        
    # BFS
    visited_edges = set()
    sequence = []
    
    for start_node in start_events:
        queue = deque([start_node])
        
        while queue:
            curr = queue.popleft()
            
            for target, name, tag in adj[curr]:
                edge = (curr, target, name)
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    queue.append(target)
                    
                    source_desc = nodes.get(curr, curr)
                    target_desc = nodes.get(target, target)
                    
                    arrow = "-> (Message) ->" if tag == 'messageFlow' else "->"
                    
                    if name:
                        sequence.append(f"{source_desc} {arrow} [Condition: {name}] -> {target_desc}")
                    else:
                        sequence.append(f"{source_desc} {arrow} {target_desc}")
                    
    # Disconnected components
    for flow in flows_list:
        source = flow.get('sourceRef')
        target = flow.get('targetRef')
        name = flow.get('name', '').strip()
        edge = (source, target, name)
        if edge not in visited_edges:
            source_desc = nodes.get(source, source)
            target_desc = nodes.get(target, target)
            arrow = "-> (Message) ->" if flow.tag == 'messageFlow' else "->"
            if name:
                sequence.append(f"{source_desc} {arrow} [Condition: {name}] -> {target_desc}")
            else:
                sequence.append(f"{source_desc} {arrow} {target_desc}")

    if sequence:
        parsed_json["Sequence"] = [f"{i+1}. {step}" for i, step in enumerate(sequence)]
    else:
        parsed_json["Sequence"] = [f"{i+1}. {step}" for i, step in enumerate(nodes.values())]
        
    return parsed_json

def parse_cml(root):
    """
    Fallback parser for generic CML or XML elements.
    It extracts anything with an 'id' and maps basic connections.
    """
    parsed_json = {
        "Process Name": "CML/XML Document",
        "Actors": [],
        "Start Events": [],
        "End Events": [],
        "Sequence": []
    }
    
    nodes = {}
    for element in root.findall('.//*'):
        node_id = None
        for attr in ['id', 'Id', 'ID', 'xml:id']:
            if attr in element.attrib:
                node_id = element.get(attr)
                break
                
        if node_id:
            name = element.get('name', element.get('Name', element.tag)).strip()
            nodes[node_id] = f"{element.tag.capitalize()}: {name}"
            
    sequence = []
    # Search for common connection tags (case insensitive)
    for link in root.findall('.//*'):
        tag_lower = link.tag.lower()
        if tag_lower in ['link', 'connection', 'association', 'flow', 'sequenceflow', 'edge', 'arc', 'transition']:
            source = link.get('source', link.get('from', link.get('sourceRef', link.get('Source'))))
            target = link.get('target', link.get('to', link.get('targetRef', link.get('Target'))))
            name = link.get('name', link.get('Name', '')).strip()
            
            if source and target:
                source_desc = nodes.get(source, source)
                target_desc = nodes.get(target, target)
                if name:
                    sequence.append(f"{source_desc} -> [{name}] -> {target_desc}")
                else:
                    sequence.append(f"{source_desc} -> {target_desc}")
                    
    if sequence:
        parsed_json["Sequence"] = [f"{i+1}. {step}" for i, step in enumerate(sequence)]
    elif nodes:
        parsed_json["Sequence"] = [f"{i+1}. {step}" for i, step in enumerate(nodes.values())]
    else:
        # Ultimate fallback: just dump all elements with text or attributes
        fallback_seq = []
        for element in root.findall('.//*'):
            tag = element.tag.capitalize()
            text = element.text.strip() if element.text else ""
            if text:
                fallback_seq.append(f"{tag}: {text}")
            elif element.attrib:
                attrs = ", ".join(f"{k}={v}" for k, v in element.attrib.items() if 'xmlns' not in k.lower())
                if attrs:
                    fallback_seq.append(f"{tag} [{attrs}]")
                    
        parsed_json["Sequence"] = [f"{i+1}. {step}" for i, step in enumerate(fallback_seq)]
        
    return parsed_json

def parse_model(file_content: str, file_type: str = "bpmn") -> str:
    """
    Parses a BPMN or XML string using the custom ElementTree parser 
    and returns a formatted JSON representation.
    """
    try:
        root = ET.fromstring(file_content.encode('utf-8'))
        root = remove_namespaces(root)
    except ET.ParseError as e:
        return json.dumps({"Error": f"Failed to parse XML: {str(e)}"})
        
    if file_type.lower() == "bpmn":
        # Additional heuristic: If no BPMN tags are found at all, fallback to CML/XML parser
        if len(root.findall('.//task')) == 0 and len(root.findall('.//startEvent')) == 0 and len(root.findall('.//sequenceFlow')) == 0:
            parsed = parse_cml(root)
        else:
            parsed = parse_bpmn(root)
    else:
        parsed = parse_cml(root)
        
    return json.dumps(parsed, indent=2)
