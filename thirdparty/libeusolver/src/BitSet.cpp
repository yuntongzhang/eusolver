// BitSet.cpp ---
// Filename: BitSet.cpp
// Author: Abhishek Udupa
// Created: Sat Oct  3 17:50:55 2015 (-0400)
//
// Copyright (c) 2013, Abhishek Udupa, University of Pennsylvania
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
// 1. Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
// 3. All advertising materials mentioning features or use of this software
//    must display the following acknowledgement:
//    This product includes software developed by The University of Pennsylvania
// 4. Neither the name of the University of Pennsylvania nor the
//    names of its contributors may be used to endorse or promote products
//    derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
// DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//

// Code:

#include <sstream>

#include "BitSet.hpp"
#include "FNVHash64.h"

namespace eusolver {

// Implementation of BitSetException
BitSetException::BitSetException() noexcept
: m_exception_info("No information.")
{
    // Nothing here
}

BitSetException::BitSetException(const BitSetException& other) noexcept
: m_exception_info(other.m_exception_info)
{
    // Nothing here
}

BitSetException::BitSetException(BitSetException&& other) noexcept
: m_exception_info(std::move(other.m_exception_info))
{
    // Nothing here
}

BitSetException::~BitSetException()
{
    // Nothing here
}

BitSetException& BitSetException::operator = (const BitSetException& other) noexcept
{
    if (&other == this) {
        return *this;
    }
    m_exception_info = other.m_exception_info;
    return *this;
}

BitSetException& BitSetException::operator = (BitSetException&& other) noexcept
{
    if (&other == this) {
        return *this;
    }
    std::swap(m_exception_info, other.m_exception_info);
    return *this;
}

const std::string& BitSetException::get_exception_info() const noexcept
{
    return m_exception_info;
}

const char* BitSetException::what() const noexcept
{
    return m_exception_info.c_str();
}


// Implementation of BitSet::BitRef
BitSet::BitRef::BitRef()
    : m_bitset_ptr(nullptr), m_bit_position(0)
{
    // Nothing here
}

BitSet::BitRef::BitRef(const BitRef& other)
    : m_bitset_ptr(other.m_bitset_ptr), m_bit_position(other.m_bit_position)
{
    // Nothing here
}

BitSet::BitRef::BitRef(BitRef&& other)
    : BitRef()
{
    std::swap(other.m_bitset_ptr, m_bitset_ptr);
    std::swap(other.m_bit_position, m_bit_position);
}

BitSet::BitRef::BitRef(BitSet* bitset_ptr, u64 bit_position)
    : m_bitset_ptr(bitset_ptr), m_bit_position(bit_position)
{
    // Nothing here
}

BitSet::BitRef::~BitRef()
{
    // Nothing here
}

BitSet::BitRef& BitSet::BitRef::operator = (const BitRef& other)
{
    if (&other == this) {
        return *this;
    }
    m_bitset_ptr = other.m_bitset_ptr;
    m_bit_position = other.m_bit_position;
    return *this;
}

BitSet::BitRef& BitSet::BitRef::operator = (BitRef&& other)
{
    if (&other == this) {
        return *this;
    }
    std::swap(m_bitset_ptr, other.m_bitset_ptr);
    std::swap(m_bit_position, other.m_bit_position);
    return *this;
}

BitSet::BitRef& BitSet::BitRef::operator = (bool value)
{
    if (value) {
        m_bitset_ptr->set_bit(m_bit_position);
    } else {
        m_bitset_ptr->clear_bit(m_bit_position);
    }
    return *this;
}

BitSet::BitRef::operator bool () const
{
    return m_bitset_ptr->test_bit(m_bit_position);
}

bool BitSet::BitRef::operator == (const BitRef& other) const
{
    return ((bool)(*this) == (bool)other);
}

bool BitSet::BitRef::operator != (const BitRef& other) const
{
    return ((bool)(*this) != (bool)other);
}

bool BitSet::BitRef::operator == (bool value) const
{
    return (bool(*this) == value);
}

bool BitSet::BitRef::operator != (bool value) const
{
    return (bool(*this) != value);
}

bool BitSet::BitRef::operator ! () const
{
    return (!((bool)(*this)));
}


// Implementation of BitSet::ConstIterator
BitSet::ConstIterator::ConstIterator()
    : m_bitset(nullptr), m_bit_position(-1)
{
    // Nothing here
}

BitSet::ConstIterator::ConstIterator(const ConstIterator& other)
    : m_bitset(other.m_bitset), m_bit_position(other.m_bit_position)
{
    // Nothing here
}

BitSet::ConstIterator::ConstIterator(const BitSet* bitset, u64 bit_position)
    : m_bitset(bitset), m_bit_position(bit_position)
{
    // Nothing here
}

BitSet::ConstIterator::~ConstIterator()
{
    // Nothing here
}

BitSet::ConstIterator& BitSet::ConstIterator::operator = (const ConstIterator& other)
{
    if (&other == this) {
        return *this;
    }

    m_bitset = other.m_bitset;
    m_bit_position = other.m_bit_position;
    return *this;
}

bool BitSet::ConstIterator::operator == (const ConstIterator& other) const
{
    return (other.m_bitset == m_bitset && other.m_bit_position == m_bit_position);
}

bool BitSet::ConstIterator::operator != (const ConstIterator& other) const
{
    return (other.m_bitset != m_bitset || other.m_bit_position != m_bit_position);
}

u64 BitSet::ConstIterator::operator * () const
{
    if (m_bit_position < 0 ||
        (u64)m_bit_position >= m_bitset->get_size_of_universe()) {
        throw BitSetException((std::string)"Attempted to dereference an un-dereferenceable " +
                              "BitSet::iterator object.");
    }
    return m_bit_position;
}

BitSet::ConstIterator& BitSet::ConstIterator::operator ++ ()
{
    m_bit_position = m_bitset->get_next_element_greater_than(m_bit_position);
    return *this;
}

BitSet::ConstIterator BitSet::ConstIterator::operator ++ (int unused)
{
    auto retval = *this;
    ++(*this);
    return retval;
}

BitSet::ConstIterator& BitSet::ConstIterator::operator -- ()
{
    m_bit_position = m_bitset->get_prev_element_lesser_than(m_bit_position);
    return *this;
}

BitSet::ConstIterator BitSet::ConstIterator::operator -- (int unused)
{
    auto retval = *this;
    --(*this);
    return retval;
}

// Implementation of BitSet
inline void BitSet::allocate(u64 size_of_universe)
{
    auto const num_words = num_words_for_bits(size_of_universe);
    m_bit_vector = (WordType*)std::calloc(num_words, sizeof(WordType));
    m_size_of_universe = size_of_universe;
}

inline void BitSet::initialize(u64 size_of_universe, bool initial_value)
{
    if (initial_value) {
        auto const num_words = num_words_for_bits(size_of_universe);
        auto const bits_allocated = num_words * bits_per_word();
        auto const rem = bits_allocated - size_of_universe;
        if (rem == 0) {
            std::memset(m_bit_vector, 0xFF, sizeof(WordType) * num_words);
        } else {
            std::memset(m_bit_vector, 0xFF, sizeof(WordType) * (num_words - 1));
            m_bit_vector[num_words - 1] = ((WordType)1 << rem) - 1;
        }
    }
}

inline void BitSet::initialize(const BitSet& other)
{
    auto const num_words = other.m_size_of_universe;
    auto src_ptr = m_bit_vector;
    auto dst_ptr = other.m_bit_vector;
    memcpy(dst_ptr, src_ptr, sizeof(WordType) * num_words);
}

inline void BitSet::check_out_of_bounds(u64 bit_position) const
{
    if (bit_position >= m_size_of_universe) {
        throw BitSetException((std::string)"Index " + std::to_string(bit_position) +
                              " was out of bounds when used to index a BitSet object.");
    }
}

inline u64 BitSet::construct_mask(u64 bit_position)
{
    u64 retval = 1;
    auto const rem = bit_position % bits_per_word();
    if (rem > 0) {
        retval <<= rem;
    }
    return retval;
}

inline void BitSet::check_equality_of_universes(const BitSet* bitset1,
                                                const BitSet* bitset2)
{
    if (bitset1->m_size_of_universe != bitset2->m_size_of_universe) {
        throw BitSetException((std::string)"Size of universes not the same in binary " +
                              "operation involving two or more BitSet objects.");
    }
}

inline void BitSet::negate_bitset(const BitSet* bitset, BitSet* result)
{
    auto const size_of_universe = bitset->m_size_of_universe;
    auto const len = num_words_for_bits(size_of_universe);
    auto const actual_num_bits = len * bits_per_word();
    auto const rem = actual_num_bits - size_of_universe;
    auto const start_ptr = bitset->m_bit_vector;
    auto const end_ptr = start_ptr + (rem == 0 ? len : (len - 1));
    auto cur_ptr = start_ptr;
    for (cur_ptr = start_ptr; cur_ptr != end_ptr; ++cur_ptr) {
        *cur_ptr = ~(*cur_ptr);
    }
    if (rem != 0) {
        u64 mask = ((u64)1 << rem) - 1;
        *cur_ptr ^= mask;
    }
    return;
}

inline void BitSet::and_with_negated_second_bitsets(const BitSet* bitset1,
                                                    const BitSet* bitset2,
                                                    BitSet* result)
{
    struct OpFun
    {
        inline WordType operator () (WordType arg1, WordType arg2) const
        {
            return (arg1 & (~arg2));
        }
    };
    apply_binary_function_on_bitsets<OpFun>(bitset1, bitset2, result);
}

inline void BitSet::and_bitsets(const BitSet* bitset1, const BitSet* bitset2, BitSet* result)
{
    struct OpFun
    {
        inline WordType operator () (WordType arg1, WordType arg2) const
        {
            return (arg1 & arg2);
        }
    };
    apply_binary_function_on_bitsets<OpFun>(bitset1, bitset2, result);
}

inline void BitSet::or_bitsets(const BitSet* bitset1, const BitSet* bitset2, BitSet* result)
{
    struct OpFun
    {
        inline WordType operator () (WordType arg1, WordType arg2) const
        {
            return (arg1 | arg2);
        }
    };

    apply_binary_function_on_bitsets<OpFun>(bitset1, bitset2, result);
}

inline void BitSet::xor_bitsets(const BitSet* bitset1, const BitSet* bitset2, BitSet* result)
{
    struct OpFun
    {
        inline WordType operator () (WordType arg1, WordType arg2) const
        {
            return (arg1 ^ arg2);
        }
    };

    apply_binary_function_on_bitsets<OpFun>(bitset1, bitset2, result);
}

BitSet::BitSet()
    : m_bit_vector(nullptr), m_size_of_universe(0)
{
    // Nothing here
}

BitSet::BitSet(const BitSet& other)
    : BitSet()
{
    allocate(other.m_size_of_universe);
    initialize(other);
}

BitSet::BitSet(BitSet&& other)
    : BitSet()
{
    std::swap(m_bit_vector, other.m_bit_vector);
    std::swap(m_size_of_universe, other.m_size_of_universe);
}

BitSet::BitSet(u64 size_of_universe)
    : BitSet(size_of_universe, false)
{
    // Nothing here
}

BitSet::BitSet(u64 size_of_universe, bool initial_value)
    : BitSet()
{
    allocate(size_of_universe);
    initialize(size_of_universe, initial_value);
}

BitSet::~BitSet()
{
    if (m_bit_vector != nullptr) {
        free(m_bit_vector);
    }
}

BitSet& BitSet::operator = (const BitSet& other)
{
    if (&other == this) {
        return *this;
    }
    if (m_bit_vector != nullptr) {
        free(m_bit_vector);
        m_bit_vector = nullptr;
    }
    allocate(other.m_size_of_universe);
    initialize(other);
    return *this;
}

BitSet& BitSet::operator = (BitSet&& other)
{
    if (&other == this) {
        return *this;
    }
    std::swap(m_bit_vector, other.m_bit_vector);
    std::swap(m_size_of_universe, other.m_size_of_universe);
    return *this;
}

bool BitSet::operator == (const BitSet& other) const
{
    if (m_size_of_universe != other.m_size_of_universe) {
        return false;
    }
    auto const len = num_words_for_bits(m_size_of_universe);
    return (memcmp(m_bit_vector, other.m_bit_vector, len * sizeof(WordType)) == 0);
}

bool BitSet::operator != (const BitSet& other) const
{
    return (!((*this) == other));
}

bool BitSet::operator < (const BitSet& other) const
{
    check_equality_of_universes(this, &other);
    auto const len = m_size_of_universe;
    auto cur_ptr_this = m_bit_vector;
    auto cur_ptr_other = other.m_bit_vector;

    bool proper = false;
    for (u64 i = 0; i < len; ++i) {
        if ((*cur_ptr_this & *cur_ptr_other) != *cur_ptr_this) {
            return false;
        }
        proper = (proper || (*cur_ptr_this != *cur_ptr_other));
        ++cur_ptr_this;
        ++cur_ptr_other;
    }
    return proper;
}

bool BitSet::operator <= (const BitSet& other) const
{
    check_equality_of_universes(this, &other);
    auto const len = m_size_of_universe;
    auto cur_ptr_this = m_bit_vector;
    auto cur_ptr_other = other.m_bit_vector;

    for (u64 i = 0; i < len; ++i) {
        if ((*cur_ptr_this & *cur_ptr_other) != *cur_ptr_this) {
            return false;
        }
        ++cur_ptr_this;
        ++cur_ptr_other;
    }
    return true;
}

bool BitSet::operator > (const BitSet& other) const
{
    return (!((*this) <= other));
}

bool BitSet::operator >= (const BitSet& other) const
{
    return (!((*this) < other));
}

void BitSet::set_bit(u64 bit_num)
{
    check_out_of_bounds(bit_num);
    auto const mask = construct_mask(bit_num);
    auto const offset = bit_num / bits_per_word();
    m_bit_vector[offset] |= mask;
}

void BitSet::clear_bit(u64 bit_num)
{
    check_out_of_bounds(bit_num);
    auto const mask = construct_mask(bit_num);
    auto const offset = bit_num / bits_per_word();
    m_bit_vector[offset] &= (~mask);
}

bool BitSet::test_bit(u64 bit_num) const
{
    check_out_of_bounds(bit_num);
    auto const mask = construct_mask(bit_num);
    auto const offset = bit_num / bits_per_word();
    return ((m_bit_vector[offset] & mask) != 0);
}

bool BitSet::flip_bit(u64 bit_num)
{
    check_out_of_bounds(bit_num);
    auto const mask = construct_mask(bit_num);
    auto const offset = bit_num / bits_per_word();
    auto const retval = ((m_bit_vector[offset] & mask) != 0);
    m_bit_vector[offset] ^= mask;
    return retval;
}

void BitSet::set_all()
{
    auto const len = num_words_for_bits(m_size_of_universe);
    auto const actual_num_bits = len * bits_per_word();
    auto const rem = actual_num_bits - m_size_of_universe;
    if (rem == 0) {
        memset(m_bit_vector, 0xFF, len * sizeof(WordType));
    } else {
        memset(m_bit_vector, 0xFF, (len - 1) * sizeof(WordType));
        const u64 mask = ((u64)1 << rem) - 1;
        m_bit_vector[len - 1] |= mask;
    }
}

void BitSet::clear_all()
{
    auto const len = num_words_for_bits(m_size_of_universe);
    memset(m_bit_vector, 0, len * sizeof(WordType));
}

void BitSet::flip_all()
{
    auto const len = num_words_for_bits(m_size_of_universe);
    auto const actual_num_bits = len * bits_per_word();
    auto const rem = actual_num_bits - m_size_of_universe;
    if (rem == 0) {
        memset(m_bit_vector, 0xFF, len * sizeof(WordType));
    } else {
        memset(m_bit_vector, 0xFF, (len - 1) * sizeof(WordType));
        const u64 mask = ((u64)1 << rem) - 1;
        m_bit_vector[len - 1] ^= mask;
    }
}

u64 BitSet::get_size_of_universe() const
{
    return m_size_of_universe;
}

u64 BitSet::length() const
{
    u64 retval = (u64)0;
    u64* first = m_bit_vector;
    u64* last = first + num_words_for_bits(m_size_of_universe);

    for (u64* current = first; current != last; ++current) {
        u64 temp = *current;
        temp = temp - ((temp >> 1) & (u64)0x5555555555555555);
        temp = (temp & (u64)0x3333333333333333) + ((temp >> 2) & (u64)0x3333333333333333);
        temp = (temp + (temp >> 4)) & (u64)0x0F0F0F0F0F0F0F0F;
        retval += ((u64)(temp * (u64)0x0101010101010101) >> 56);
    }

    return retval;
}

u64 BitSet::size() const
{
    return length();
}

bool BitSet::is_full() const
{
    auto const len = num_words_for_bits(m_size_of_universe);
    auto const actual_num_bits = len * bits_per_word();
    auto const rem = actual_num_bits - m_size_of_universe;
    auto const max_index = ((rem == 0) ? len : (len - 1));
    const u64 all_ones_mask = ((((WordType)1 << (bits_per_word() - 1)) - 1) << 1) | 1;
    for (u64 i = 0; i < max_index; ++i) {
        if (m_bit_vector[i] != all_ones_mask) {
            return false;
        }
    }
    if (rem != 0) {
        auto const mask = ((u64)1 << rem) - 1;
        return ((m_bit_vector[len - 1] & mask) == mask);
    }
    return true;
}

bool BitSet::is_empty() const
{
    auto const len = num_words_for_bits(m_size_of_universe);
    for (u64 i = 0; i < len; ++i) {
        if (m_bit_vector[i] != (u64)0) {
            return false;
        }
    }
    return true;
}

BitSet BitSet::operator & (const BitSet& other) const
{
    BitSet retval(m_size_of_universe);
    and_bitsets(this, &other, &retval);
    return retval;
}

BitSet BitSet::operator | (const BitSet& other) const
{
    BitSet retval(m_size_of_universe);
    or_bitsets(this, &other, &retval);
    return retval;
}

BitSet BitSet::operator ^ (const BitSet& other) const
{
    BitSet retval(m_size_of_universe);
    xor_bitsets(this, &other, &retval);
    return retval;
}

BitSet BitSet::operator ~ () const
{
    BitSet retval(m_size_of_universe);
    negate_bitset(this, &retval);
    return retval;
}

BitSet BitSet::operator ! () const
{
    return (~(*this));
}

BitSet BitSet::operator - (const BitSet& other) const
{
    BitSet retval(m_size_of_universe);
    and_with_negated_second_bitsets(this, &other, &retval);
    return retval;
}

BitSet& BitSet::operator &= (const BitSet& other)
{
    and_bitsets(this, &other, this);
    return *this;
}

BitSet& BitSet::operator |= (const BitSet& other)
{
    or_bitsets(this, &other, this);
    return *this;
}

BitSet& BitSet::operator ^= (const BitSet& other)
{
    xor_bitsets(this, &other, this);
    return *this;
}

BitSet& BitSet::operator -= (const BitSet& other)
{
    and_with_negated_second_bitsets(this, &other, this);
    return *this;
}

BitSet* BitSet::intersection_with(const BitSet* other) const
{
    check_equality_of_universes(this, other);
    auto retval = new BitSet(m_size_of_universe);
    and_bitsets(this, other, retval);
    return retval;
}

void BitSet::intersect_with_in_place(const BitSet* other)
{
    and_bitsets(this, other, this);
}

BitSet* BitSet::union_with(const BitSet* other) const
{
    check_equality_of_universes(this, other);
    auto retval = new BitSet(m_size_of_universe);
    or_bitsets(this, other, retval);
    return retval;
}

void BitSet::union_with_in_place(const BitSet* other)
{
    or_bitsets(this, other, this);
}

BitSet* BitSet::symmetric_difference_with(const BitSet* other) const
{
    check_equality_of_universes(this, other);
    auto retval = new BitSet(m_size_of_universe);
    xor_bitsets(this, other, retval);
    return retval;
}

void BitSet::symmetric_difference_with_in_place(const BitSet* other)
{
    xor_bitsets(this, other, this);
}

BitSet* BitSet::negate() const
{
    auto retval = new BitSet(m_size_of_universe);
    negate_bitset(this, retval);
    return retval;
}

void BitSet::negate_in_place()
{
    negate_bitset(this, this);
}

BitSet* BitSet::difference_with(const BitSet* other) const
{
    check_equality_of_universes(this, other);
    auto retval = new BitSet(m_size_of_universe);
    and_with_negated_second_bitsets(this, other, retval);
    return retval;
}

void BitSet::difference_with_in_place(const BitSet* other)
{
    and_with_negated_second_bitsets(this, other, this);
}

bool BitSet::operator [] (u64 position) const
{
    return test_bit(position);
}

BitSet::BitRef BitSet::operator [] (u64 position)
{
    check_out_of_bounds(position);
    return BitRef(this, position);
}

bool BitSet::at(u64 bit_num) const
{
    return test_bit(bit_num);
}

BitSet::BitRef BitSet::at(u64 bit_num)
{
    return (*this)[bit_num];
}

BitSet::Iterator BitSet::begin() const
{
    auto first = get_next_element_greater_than_or_equal_to(0);
    return Iterator(this, first);
}

BitSet::Iterator BitSet::end() const
{
    return Iterator(this, m_size_of_universe);
}

void BitSet::insert(u64 bit_num)
{
    set_bit(bit_num);
}

void BitSet::erase(u64 bit_num)
{
    clear_bit(bit_num);
}

void BitSet::erase(const Iterator& position)
{
    clear_bit(position.m_bit_position);
}

void BitSet::clear()
{
    clear_all();
}

i64 BitSet::get_next_element_greater_than_or_equal_to(u64 position) const
{
    if (position >= m_size_of_universe) {
        return position;
    }

    auto const len = num_words_for_bits(m_size_of_universe);
    auto offset = position / bits_per_word();
    auto bit_position = position % bits_per_word();
    u64 mask = ((bit_position != 0) ? ((u64)1 << bit_position) : (u64)1);
    while (bit_position < bits_per_word()) {
        if ((m_bit_vector[offset] & mask) != 0) {
            return ((offset * bits_per_word()) + bit_position);
        }
        mask <<= 1;
    }
    ++offset;

    // We're now at a word boundary
    while (m_bit_vector[offset] == 0 && offset < len) {
        ++offset;
    }

    if (offset >= len) {
        return m_size_of_universe;
    }

    bit_position = 0;
    mask = 1;
    while (bit_position < bits_per_word()) {
        if ((m_bit_vector[offset] & mask) != 0) {
            return ((offset * bits_per_word()) + bit_position);
        }
        mask <<= 1;
    }
    // should never come here!
    throw BitSetException((std::string)"Internal Error: Unreachable code hit in call to "
                          "BitSet::get_next_element_greater_than_or_equal_to()");
    return 0;
}

i64 BitSet::get_next_element_greater_than(u64 position) const
{
    return get_next_element_greater_than_or_equal_to(position + 1);
}

i64 BitSet::get_prev_element_lesser_than_or_equal_to(u64 position) const
{
    if (position == 0 && test_bit(0)) {
        return 0;
    }

    position = std::min(position, m_size_of_universe - 1);

    i64 offset = position / bits_per_word();
    i64 bit_position = position % bits_per_word();
    u64 mask = ((bit_position != 0) ? ((u64)1 << bit_position) : (u64)1);
    while (bit_position >= 0) {
        if ((m_bit_vector[offset] & mask) != 0) {
            return ((offset * bits_per_word()) + bit_position);
        }
        mask >>= 1;
    }

    --offset;
    // we're at a word boundary
    while (m_bit_vector[offset] == 0 && offset >= 0) {
        --offset;
    }

    if (offset < 0) {
        return -1;
    }

    bit_position = bits_per_word() - 1;
    mask = ((WordType)1 << bit_position);
    while (bit_position >= 0) {
        if ((m_bit_vector[offset] & mask) != 0) {
            return ((offset * bits_per_word()) + bit_position);
        }
        mask >>= 1;
    }

    // should never be reached
    throw BitSetException((std::string)"Internal Error: Unreachable code hit in call to "
                          "BitSet::get_prev_element_lesser_than_or_equal_to()");
    return 0;
}

i64 BitSet::get_prev_element_lesser_than(u64 position) const
{
    if (position == 0) {
        return -1;
    }
    return get_prev_element_lesser_than_or_equal_to(position - 1);
}

u64 BitSet::hash() const
{
    return fnv_64a_buf(m_bit_vector,
                       sizeof(WordType) * num_words_for_bits(m_size_of_universe),
                       FNV1A_64_INIT);
}

std::string BitSet::to_string() const
{
    std::ostringstream sstr;
    sstr << "BitSet(" << m_size_of_universe << "): {";
    bool printed_one = false;
    for (u64 i = 0; i < m_size_of_universe; ++i) {
        if (test_bit(i)) {
            if (printed_one) {
                sstr << ", ";
            }
            sstr << i;
            printed_one = true;
        }
    }
    sstr << "}";
    return sstr.str();
}

BitSet* BitSet::clone() const
{
    return new BitSet(*this);
}

} /* end namespace eusolver */

//
// BitSet.cpp ends here
