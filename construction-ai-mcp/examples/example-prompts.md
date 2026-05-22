# Example Prompts for Construction AI

Copy and paste these into Claude Desktop to test the Construction AI MCP server.

---

## Basic Room Estimates

### Example 1: Simple Office
```
Estimate drywall for a 12x10 office with 8ft ceilings, 
one 3x7 door, and one 3x4 window. Level 4 finish.
```

**Expected Output:**
- ~288 sqft wall area
- ~8-10 drywall sheets
- Labor hours breakdown
- Total cost estimate

---

### Example 2: Large Conference Room
```
Estimate drywall for a 30x20 conference room with 10ft ceilings,
two 3x7 doors, and six 4x3 windows. Level 4 commercial finish.
```

**Expected Output:**
- ~800+ sqft wall area
- 600 sqft ceiling area
- Materials for 1,400+ total sqft
- Commercial labor rates

---

### Example 3: High-End Residential
```
Estimate drywall for a 25x18 living room with 12ft ceilings,
one 8x8 opening to dining room, two 6x4 windows. 
Use Level 5 finish for premium quality.
```

**Expected Output:**
- Higher compound amounts (Level 5)
- More finishing hours
- Premium pricing
- Cost per sqft higher than Level 4

---

## Multi-Room Projects

### Example 4: Three Office Suite
```
I need drywall estimates for three offices:

Office 1: 12x10 feet, 9ft ceiling, one door, one window
Office 2: 15x12 feet, 9ft ceiling, one door, two windows  
Office 3: 14x11 feet, 9ft ceiling, one door, one window

All need Level 4 commercial finish. What's the total estimate?
```

**Expected Output:**
- Separate calculation for each room
- Combined totals
- Bulk material quantities
- Total labor hours across all three

---

### Example 5: Full House Addition
```
Estimate drywall for a house addition:

Bedroom 1: 14x12, 8ft ceiling, one door, two windows
Bedroom 2: 12x11, 8ft ceiling, one door, one window
Bathroom: 8x7, 8ft ceiling, one door, no windows
Hallway: 20x4, 8ft ceiling, three doorways

Level 3 finish for residential work.
```

**Expected Output:**
- Room-by-room breakdown
- Different finish level pricing
- Residential labor rates
- Total project cost

---

## Complex Wall Descriptions

### Example 6: From Floor Plan
```
I have an office renovation with these walls:

North wall: 40 feet long, 9 feet high, has four 3x7 doors
South wall: 40 feet long, 9 feet high, no openings
East wall: 30 feet long, 9 feet high, has three 4x3 windows
West wall: 30 feet long, 9 feet high, no openings

Plus ceiling: 1,200 square feet

Commercial Level 4 finish. What's the estimate?
```

**Expected Output:**
- ~1,080 sqft wall area (after deductions)
- 1,200 sqft ceiling area
- Total: 2,280 sqft
- Materials for large commercial project
- Multiple day labor estimate

---

### Example 7: Retail Space
```
Estimate drywall for a retail space:

Front wall: 50ft x 10ft, large 12x8 storefront window
Back wall: 50ft x 10ft, one 3x7 door to storage
Left wall: 30ft x 10ft, no openings
Right wall: 30ft x 10ft, two 3x7 doors (restrooms)

No ceiling work needed. Level 4 commercial finish.
```

**Expected Output:**
- Walls only (no ceiling)
- Large opening deduction for storefront
- Commercial pricing
- Retail project type consideration

---

## Different Finish Levels

### Example 8: Level 0 (Garage/Warehouse)
```
Estimate drywall for a warehouse storage area:
40x30 space, 12ft walls, no ceiling, no windows, one large door.
Level 0 finish - just hung, no taping needed.
```

**Expected Output:**
- Minimal compound/tape
- Reduced finishing labor
- Lower cost per sqft
- Industrial rates

---

### Example 9: Level 5 (High-End)
```
Estimate drywall for a luxury home media room:
20x16 room, 10ft ceiling, one door, no windows.
Level 5 finish with skim coat for perfect walls.
```

**Expected Output:**
- Maximum compound usage
- Extensive finishing hours
- Higher labor costs
- Premium pricing

---

## Different Project Types

### Example 10: Medical Facility
```
Estimate drywall for a medical office exam room:
12x10 room, 9ft ceiling, one door, one window.
Medical facility grade, Level 4 finish.
```

**Expected Output:**
- Higher labor rates (medical project type)
- Stricter quality standards
- Premium pricing

---

### Example 11: Industrial
```
Estimate drywall for an industrial office in a factory:
15x12 office, 9ft ceiling, one door, one window.
Industrial project type, Level 3 finish.
```

**Expected Output:**
- Industrial labor rates
- Standard quality
- Practical pricing

---

## Edge Cases & Special Scenarios

### Example 12: Ceiling Only
```
Estimate drywall for ceiling replacement only:
25x20 room, 9ft ceiling height, no wall work needed.
Level 4 finish.
```

**Expected Output:**
- Ceiling materials only
- Hanging/taping/finishing for horizontal surface
- Ceiling-specific labor rates (slower than walls)

---

### Example 13: Walls Only
```
Estimate drywall for wall repairs (no ceiling):
Replacing drywall on two walls:
- Wall 1: 15ft x 8ft, one window
- Wall 2: 12ft x 8ft, no openings
Level 4 finish to match existing.
```

**Expected Output:**
- Wall materials only
- Patch/repair consideration
- Finish matching labor

---

### Example 14: Partition Walls
```
Estimate drywall for new partition walls in open office:
Creating 5 partition walls, each 10ft long, 9ft high.
Both sides need drywall. No doors or windows.
Level 4 commercial finish.
```

**Expected Output:**
- Double-sided wall calculations
- Material quantities for both sides
- Labor for both sides
- Total cost for partitions

---

### Example 15: Very Large Project
```
Estimate drywall for entire floor of office building:

10 private offices: each 12x10, 9ft ceiling, one door, one window
3 conference rooms: each 20x15, 9ft ceiling, two doors, four windows
Reception area: 30x20, 9ft ceiling, one main door, no windows
Kitchen: 15x12, 9ft ceiling, two doors, no windows
2 Restrooms: each 10x8, 9ft ceiling, one door, no windows
Hallways: 200 linear feet, 9ft high, 8 doorways total

All ceilings included. Level 4 commercial finish.
```

**Expected Output:**
- Comprehensive breakdown by area type
- Large material quantities
- Multi-week labor estimate
- Substantial total cost
- Detailed project summary

---

## Testing Different Features

### Example 16: Clarification Test
```
Estimate drywall for a room
```

**Expected Response:**
Claude should ask for:
- Room dimensions
- Ceiling height
- Doors/windows
- Finish level
- Project type

---

### Example 17: Conversational Follow-Up
```
First: "Estimate drywall for 12x10 office, 8ft ceiling, one door, one window, Level 4"
Then: "What if we change to Level 5 finish?"
Then: "And add another window?"
```

**Expected Response:**
Claude should maintain context and recalculate with changes.

---

### Example 18: Units Clarification
```
Estimate drywall for a 6x4 meter room with 3 meter ceilings
```

**Expected Response:**
Claude should convert or ask for clarification (MCP server uses feet).

---

## Comparison Prompts

### Example 19: Compare Finish Levels
```
Compare Level 3, Level 4, and Level 5 finish costs 
for a 15x12 office with 9ft ceilings, one door, one window.
```

**Expected Output:**
- Three separate estimates
- Cost differences highlighted
- Labor hour differences
- Material quantity differences

---

### Example 20: Compare Project Types
```
Estimate drywall for 12x10 office, 9ft ceiling, one door, one window.
Show me the cost difference between:
- Residential project
- Commercial project  
- Medical facility project
```

**Expected Output:**
- Three estimates with different labor rates
- Price variance by project type
- Explanation of differences

---

## Tips for Best Results

1. **Be Specific:** Include dimensions, ceiling height, openings
2. **Specify Finish Level:** Level 4 is standard commercial
3. **Mention Project Type:** Affects labor rates
4. **Natural Language:** Claude understands conversational requests
5. **Ask Follow-ups:** Claude maintains context for iterations

---

## Common Questions to Ask

```
"What finish level should I use for an office?"
"How much does Level 5 cost compared to Level 4?"
"What's included in the labor estimate?"
"How accurate is this estimate?"
"Can I adjust the overhead and profit percentages?"
```

---

## Feedback & Issues

If an estimate seems wrong:
1. Check your inputs (room size, openings)
2. Verify finish level is appropriate
3. Consider project type affects pricing
4. Report issues: cooperxxjohn@gmail.com

---

Happy estimating! 🏗️
