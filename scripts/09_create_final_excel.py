import pandas as pd
import os

def create_final_excel(input_csv="jobs.csv", output_excel="final_ranked_jobs.xlsx"):
    print(f"📊 Reading {input_csv}...")
    
    if not os.path.exists(input_csv):
        print(f"❌ File not found: {input_csv}")
        return

    df = pd.read_csv(input_csv)
    print(f"✅ Loaded {len(df)} jobs")
    
    # Sort by suitability score
    if 'suitability_score' in df.columns:
        df = df.sort_values(by='suitability_score', ascending=False)
        print("✅ Sorted by suitability score")
    
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # 1. All Jobs (World)
        df.to_excel(writer, sheet_name='All Jobs (World)', index=False)
        print("✅ Created 'All Jobs (World)' sheet")
        
        # 2. Region-specific sheets
        # Special handling for UK to catch jobs found in WORLDWIDE search but located in UK
        uk_keywords = ['United Kingdom', 'UK', 'London', 'England', 'Scotland', 'Wales', 'Northern Ireland', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow', 'Edinburgh', 'Bristol', 'Liverpool']
        uk_pattern = '|'.join(uk_keywords)
        
        # Create mask for UK jobs (Region is UK OR Location contains UK keywords)
        uk_mask = (df['region'] == 'United Kingdom') | \
                  (df['location'].str.contains(uk_pattern, case=False, na=False))
        
        uk_df = df[uk_mask]
        if not uk_df.empty:
            uk_df.to_excel(writer, sheet_name='United Kingdom Jobs', index=False)
            print(f"✅ Created 'United Kingdom Jobs' sheet ({len(uk_df)} jobs)")
            
        # Handle other regions if any (excluding UK since we just handled it)
        if 'region' in df.columns:
            regions = df['region'].unique()
            for region in regions:
                if pd.isna(region) or str(region).upper() in ['WORLDWIDE', 'WORLD', 'NAN', 'NONE', 'UNITED KINGDOM']:
                    continue
                
                # Filter
                region_df = df[df['region'] == region]
                
                # Clean sheet name
                sheet_name = f"{str(region)[:20]} Jobs"
                sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_'))
                
                region_df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✅ Created '{sheet_name}' sheet ({len(region_df)} jobs)")
        
    print(f"\n🎉 Excel file saved: {output_excel}")

if __name__ == "__main__":
    create_final_excel()
