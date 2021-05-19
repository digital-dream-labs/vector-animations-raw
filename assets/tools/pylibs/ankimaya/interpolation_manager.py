import maya.cmds as mc


def find_value_for_frame(current_frame, all_frames, ctr_attr):
    """
    Finds what value should be assigned to a frame based on
    linear interpolation. This function assumes that the
    provided list of frame numbers is sorted.
    """
    # In case there is no last or first frame, the frame is the same as first or last
    if current_frame >= max(all_frames):
        return mc.getAttr(ctr_attr, time=max(all_frames))
    elif current_frame <= min(all_frames):
        return mc.getAttr(ctr_attr, time=min(all_frames))
    else:
        prev_frame = get_closest_prev_frame(current_frame, all_frames)
        next_frame = get_closest_next_frame(current_frame, all_frames)
        frame_delta = next_frame - prev_frame
        prev_value = mc.getAttr(ctr_attr, time=prev_frame)
        next_value = mc.getAttr(ctr_attr, time=next_frame)
        value_delta = next_value - prev_value
        current_value = prev_value + (current_frame - prev_frame) * (value_delta / frame_delta)
        return current_value


def get_closest_prev_frame(current_frame, frames_list):
    """
    Returns the frame that's closest to the frame provided in
    the list of frames (favor previous)
    """
    for i, frame_num in enumerate(frames_list):
        if frame_num == current_frame:
            return current_frame
        elif frame_num > current_frame:
            if i == 0:
                return frames_list[i]
            else:
                return frames_list[i-1]
    return min(frames_list)


def get_closest_next_frame(current_frame, frames_list):
    """
    Returns the frame that's closest to the frame provided in
    the list of frames (favor next)
    """
    for i in range(len(frames_list) - 1, -1, -1):
        frame_num = frames_list[i]
        if frame_num == current_frame:
            return current_frame
        elif frame_num < current_frame:
            if i == (len(frames_list) - 1):
                return frames_list[i]
            else:
                return frames_list[i+1]
    return max(frames_list)