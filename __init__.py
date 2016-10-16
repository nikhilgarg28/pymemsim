from .block import Block
from .tracker import Tracker
from .cache import Store

_t = Tracker()
L2 = Store('L2 cache', 1 << 11, 1 << 7, 20, assoc=8, tracker=_t)
L1 = Store('L1 cache', 64, 64, 1, tracker=_t)

def p_load_mem(p_addr):
    if p_addr in L1:
        return L1[p_addr]

    if p_addr in L2:
        L1[p_addr] = L2[p_addr]
        return L1[p_addr]

    if p_addr in RAM:
        L1[p_addr] = L2[p_addr] = RAM[p_addr]
        return L1[p_addr]

    #declare page fault
    #load data from disk swap
    #return

def v_load_mem(v_addr):
    p_addr = translate_addr(v_addr)
    return p_load_mem(p_addr)


def translate_addr(v_addr):
    v_page, v_offset = split(v_addr, PAGE_SIZE)
    p_page = translate_page(v_page)
    return p_page + v_offset

def translate_page(v_page):
    if v_page in TLB:
        return TLB[v_page]

    pt_l1_offset, pt_l2_offset, offset = split(v_page)

    pt_l1_base = p_load_mem(PGD)
    pt_l2_base = p_load_mem(pt_l1_base + pt_l1_offset)
    pt_l3_base = p_load_mem(pt_l2_base + pt_l2_offset)
    return p_load_mem(pt_l3_base + offset)


def context_switch():
    TLB.clear()
