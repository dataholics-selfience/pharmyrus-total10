"""
Pipeline Service v3.0 - Complete Patent Intelligence Pipeline
Executes parallel searches across 6 data sources with rich debug output
"""
import asyncio
import aiohttp
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class PipelineService:
    """Orchestrates complete patent search pipeline"""
    
    def __init__(self):
        self.serp_api_key = "3f22448f4d43ce8259fa2f7f6385222323a67c4ce4e72fcc774b43d23812889d"
        self.inpi_api = "https://crawler3-production.up.railway.app/api/data/inpi/patents"
        self.fda_api = "https://api.fda.gov/drug"
        self.clinical_trials_api = "https://clinicaltrials.gov/api/v2/studies"
        self.pubchem_api = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        
    async def execute_full_pipeline(
        self,
        molecule: str,
        country_filter: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Execute complete 6-layer pipeline with parallel processing"""
        
        start_time = time.time()
        debug_layers = []
        
        # Layer 1: PubChem - Get synonyms and chemical data
        layer1_start = time.time()
        pubchem_data = await self._layer1_pubchem(molecule)
        layer1_duration = time.time() - layer1_start
        debug_layers.append({
            "layer": "Layer 1: PubChem",
            "status": "success" if pubchem_data.get("cid") else "partial",
            "duration_seconds": round(layer1_duration, 2),
            "data_points": len(pubchem_data.get("synonyms", [])),
            "details": f"Found {len(pubchem_data.get('dev_codes', []))} dev codes, {len(pubchem_data.get('synonyms', []))} synonyms"
        })
        
        # Layer 2: Google Patents WO Discovery (parallel queries)
        layer2_start = time.time()
        wo_numbers = await self._layer2_discover_wos(molecule, pubchem_data)
        layer2_duration = time.time() - layer2_start
        debug_layers.append({
            "layer": "Layer 2: WO Discovery",
            "status": "success" if wo_numbers else "no_results",
            "duration_seconds": round(layer2_duration, 2),
            "data_points": len(wo_numbers),
            "details": f"Found {len(wo_numbers)} WO patents from 13+ parallel queries"
        })
        
        # Limit WO numbers if requested
        wo_numbers_limited = wo_numbers[:limit]
        
        # Layers 3-6: Parallel execution
        layer3_start = time.time()
        
        # Execute all layers in parallel
        results = await asyncio.gather(
            self._layer3_patent_details(wo_numbers_limited, country_filter),
            self._layer4_inpi_brasil(molecule, pubchem_data),
            self._layer5_fda_data(molecule),
            self._layer6_clinical_trials(molecule),
            return_exceptions=True
        )
        
        patent_details, inpi_patents, fda_data, clinical_data = results
        layer3_duration = time.time() - layer3_start
        
        # Debug for Layer 3
        if isinstance(patent_details, Exception):
            patent_details = {"patents": [], "errors": [str(patent_details)]}
        debug_layers.append({
            "layer": "Layer 3: Patent Details",
            "status": "success" if patent_details.get("patents") else "no_results",
            "duration_seconds": round(layer3_duration, 2),
            "data_points": len(patent_details.get("patents", [])),
            "details": f"Processed {len(wo_numbers_limited)} WO patents"
        })
        
        # Debug for Layer 4
        if isinstance(inpi_patents, Exception):
            inpi_patents = {"br_patents": [], "errors": [str(inpi_patents)]}
        debug_layers.append({
            "layer": "Layer 4: INPI Brasil",
            "status": "success" if inpi_patents.get("br_patents") else "no_results",
            "duration_seconds": round(layer3_duration, 2),  # Same parallel window
            "data_points": len(inpi_patents.get("br_patents", [])),
            "details": f"Found {len(inpi_patents.get('br_patents', []))} BR patents"
        })
        
        # Debug for Layer 5
        if isinstance(fda_data, Exception):
            fda_data = {"approval_status": "Error", "errors": [str(fda_data)]}
        debug_layers.append({
            "layer": "Layer 5: FDA",
            "status": "success" if fda_data.get("approval_status") != "Error" else "error",
            "duration_seconds": round(layer3_duration, 2),
            "data_points": len(fda_data.get("applications", [])),
            "details": f"FDA Status: {fda_data.get('approval_status', 'Unknown')}"
        })
        
        # Debug for Layer 6
        if isinstance(clinical_data, Exception):
            clinical_data = {"total_trials": 0, "errors": [str(clinical_data)]}
        debug_layers.append({
            "layer": "Layer 6: Clinical Trials",
            "status": "success" if clinical_data.get("total_trials", 0) > 0 else "no_results",
            "duration_seconds": round(layer3_duration, 2),
            "data_points": clinical_data.get("total_trials", 0),
            "details": f"Found {clinical_data.get('total_trials', 0)} clinical trials"
        })
        
        # Aggregate all patents
        all_patents = self._aggregate_patents(patent_details, inpi_patents)
        
        # Build executive summary
        total_duration = time.time() - start_time
        executive_summary = self._build_executive_summary(
            molecule,
            pubchem_data,
            all_patents,
            fda_data,
            clinical_data
        )
        
        # Build comprehensive response
        response = {
            "executive_summary": executive_summary,
            "pubchem_data": pubchem_data,
            "search_strategy": {
                "pipeline_version": "3.0",
                "execution_mode": "parallel_batch",
                "layers_executed": ["PubChem", "Google Patents", "WIPO", "INPI", "FDA", "ClinicalTrials"],
                "total_wo_patents": len(wo_numbers),
                "wo_patents_processed": len(wo_numbers_limited),
                "country_filter": country_filter or "ALL",
                "parallel_processing": True,
                "sources": {
                    "pubchem": "NIH PubChem API",
                    "google_patents": "SerpAPI Google Patents",
                    "wipo": "WIPO Patentscope Crawler",
                    "inpi": "INPI Brasil API",
                    "fda": "FDA API",
                    "clinical_trials": "ClinicalTrials.gov API v2"
                }
            },
            "wo_patents": patent_details.get("patents", []),
            "br_patents_inpi": inpi_patents.get("br_patents", []),
            "all_patents": all_patents,
            "fda_data": fda_data,
            "clinical_trials_data": clinical_data,
            "debug_info": {
                "total_duration_seconds": round(total_duration, 2),
                "layers": debug_layers,
                "timings": {
                    "pubchem": round(layer1_duration, 2),
                    "wo_discovery": round(layer2_duration, 2),
                    "parallel_batch": round(layer3_duration, 2),
                    "total": round(total_duration, 2)
                },
                "errors_count": sum(1 for layer in debug_layers if layer["status"] == "error"),
                "warnings_count": sum(1 for layer in debug_layers if layer["status"] in ["partial", "no_results"]),
                "errors": [],
                "warnings": []
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return response
    
    async def _layer1_pubchem(self, molecule: str) -> Dict[str, Any]:
        """Layer 1: Fetch PubChem data"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get synonyms
                url = f"{self.pubchem_api}/compound/name/{molecule}/synonyms/JSON"
                async with session.get(url, timeout=30) as resp:
                    if resp.status != 200:
                        return {"error": "PubChem not found"}
                    
                    data = await resp.json()
                    synonyms = data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
                    
                    # Extract dev codes and CAS
                    dev_codes = []
                    cas_number = None
                    
                    dev_pattern = re.compile(r'^[A-Z]{2,5}-?\d{3,7}[A-Z]?$', re.I)
                    cas_pattern = re.compile(r'^\d{2,7}-\d{2}-\d$')
                    
                    for syn in synonyms[:100]:  # Limit to first 100
                        if dev_pattern.match(syn) and len(dev_codes) < 20:
                            dev_codes.append(syn)
                        if cas_pattern.match(syn) and not cas_number:
                            cas_number = syn
                    
                    # Get chemical properties
                    cid_url = f"{self.pubchem_api}/compound/name/{molecule}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,InChI,InChIKey/JSON"
                    properties = {}
                    try:
                        async with session.get(cid_url, timeout=30) as prop_resp:
                            if prop_resp.status == 200:
                                prop_data = await prop_resp.json()
                                props = prop_data.get("PropertyTable", {}).get("Properties", [{}])[0]
                                properties = {
                                    "cid": props.get("CID"),
                                    "molecular_formula": props.get("MolecularFormula"),
                                    "molecular_weight": props.get("MolecularWeight"),
                                    "iupac_name": props.get("IUPACName"),
                                    "canonical_smiles": props.get("CanonicalSMILES"),
                                    "inchi": props.get("InChI"),
                                    "inchi_key": props.get("InChIKey")
                                }
                    except:
                        pass
                    
                    return {
                        "cid": properties.get("cid"),
                        "synonyms": synonyms[:50],  # Top 50 synonyms
                        "dev_codes": dev_codes,
                        "cas_number": cas_number,
                        **properties
                    }
        except Exception as e:
            return {"error": str(e), "synonyms": [], "dev_codes": []}
    
    async def _layer2_discover_wos(self, molecule: str, pubchem_data: Dict) -> List[str]:
        """Layer 2: Discover WO patent numbers via parallel Google Patents queries"""
        
        # Build multiple search queries
        queries = []
        
        # Year-based queries
        for year in range(2011, 2025):
            queries.append(f"{molecule} patent WO{year}")
        
        # Dev code queries
        for dev_code in pubchem_data.get("dev_codes", [])[:3]:
            queries.append(f"{dev_code} patent WO")
        
        # Company queries
        queries.append(f"{molecule} Orion Corporation patent")
        queries.append(f"{molecule} Bayer patent")
        
        # Execute all queries in parallel
        async with aiohttp.ClientSession() as session:
            tasks = []
            for query in queries[:15]:  # Limit to 15 parallel queries
                url = f"https://serpapi.com/search.json"
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": self.serp_api_key,
                    "num": 10
                }
                tasks.append(self._fetch_search(session, url, params))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract WO numbers
        wo_pattern = re.compile(r'WO[\s-]?(\d{4})[\s/]?(\d{6})', re.I)
        wo_numbers = set()
        
        for result in results:
            if isinstance(result, dict):
                for item in result.get("organic_results", []):
                    text = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('link', '')}"
                    matches = wo_pattern.findall(text)
                    for year, num in matches:
                        wo_numbers.add(f"WO{year}{num}")
        
        return sorted(list(wo_numbers))
    
    async def _fetch_search(self, session: aiohttp.ClientSession, url: str, params: Dict) -> Dict:
        """Helper to fetch search results"""
        try:
            async with session.get(url, params=params, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except:
            return {}
    
    async def _layer3_patent_details(self, wo_numbers: List[str], country_filter: Optional[str]) -> Dict:
        """Layer 3: Fetch detailed patent information for all WO numbers"""
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for wo in wo_numbers:
                # Call our existing WIPO endpoint
                url = f"https://pharmyrus-total10-production-9785.up.railway.app/api/v1/wipo/{wo}"
                if country_filter:
                    url += f"?country={country_filter}"
                tasks.append(self._fetch_patent_detail(session, url, wo))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        patents = []
        for result in results:
            if isinstance(result, dict) and result.get("publication_number"):
                patents.append(result)
        
        return {"patents": patents, "total": len(patents)}
    
    async def _fetch_patent_detail(self, session: aiohttp.ClientSession, url: str, wo: str) -> Dict:
        """Fetch single patent detail"""
        try:
            async with session.get(url, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                return {}
        except:
            return {}
    
    async def _layer4_inpi_brasil(self, molecule: str, pubchem_data: Dict) -> Dict:
        """Layer 4: Search INPI Brasil"""
        
        search_terms = [molecule]
        search_terms.extend(pubchem_data.get("dev_codes", [])[:5])
        if pubchem_data.get("cas_number"):
            search_terms.append(pubchem_data["cas_number"])
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for term in search_terms[:10]:  # Max 10 searches
                url = f"{self.inpi_api}?medicine={term}"
                tasks.append(self._fetch_inpi(session, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Deduplicate BR patents
        br_patents = {}
        for result in results:
            if isinstance(result, dict):
                for patent in result.get("data", []):
                    pub_num = patent.get("title", "").replace(" ", "-")
                    if pub_num.startswith("BR") and pub_num not in br_patents:
                        br_patents[pub_num] = {
                            "publication_number": pub_num,
                            "title": patent.get("applicant", ""),
                            "filing_date": patent.get("depositDate", ""),
                            "abstract": patent.get("fullText", "")[:300],
                            "source": "INPI Brasil",
                            "link": f"https://busca.inpi.gov.br/pePI/servlet/PatenteServletController?Action=detail&CodPedido={pub_num}"
                        }
        
        return {"br_patents": list(br_patents.values()), "total": len(br_patents)}
    
    async def _fetch_inpi(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Fetch INPI data"""
        try:
            async with session.get(url, timeout=40) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except:
            return {}
    
    async def _layer5_fda_data(self, molecule: str) -> Dict:
        """Layer 5: Fetch FDA approval data"""
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search NDC
                url = f"{self.fda_api}/ndc.json"
                params = {"search": f'generic_name:"{molecule}"', "limit": 5}
                
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return {"approval_status": "Not Found", "applications": []}
                    
                    data = await resp.json()
                    results = data.get("results", [])
                    
                    applications = []
                    for r in results:
                        applications.append({
                            "product_ndc": r.get("product_ndc"),
                            "brand_name": r.get("brand_name"),
                            "generic_name": r.get("generic_name"),
                            "labeler_name": r.get("labeler_name"),
                            "dosage_form": r.get("dosage_form"),
                            "route": r.get("route", []),
                            "marketing_category": r.get("marketing_category"),
                            "application_number": r.get("application_number")
                        })
                    
                    return {
                        "approval_status": "Approved" if applications else "Not Found",
                        "applications": applications,
                        "total_products": len(applications)
                    }
        except Exception as e:
            return {"approval_status": "Error", "error": str(e), "applications": []}
    
    async def _layer6_clinical_trials(self, molecule: str) -> Dict:
        """Layer 6: Fetch clinical trials data"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.clinical_trials_api}"
                params = {
                    "query.term": molecule,
                    "pageSize": 20
                }
                
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        return {"total_trials": 0, "trials": []}
                    
                    data = await resp.json()
                    studies = data.get("studies", [])
                    
                    # Aggregate data
                    by_phase = {}
                    by_status = {}
                    sponsors = set()
                    countries = set()
                    
                    trials = []
                    for study in studies:
                        protocol = study.get("protocolSection", {})
                        identification = protocol.get("identificationModule", {})
                        status_module = protocol.get("statusModule", {})
                        design_module = protocol.get("designModule", {})
                        
                        phase = design_module.get("phases", ["Unknown"])[0] if design_module.get("phases") else "Unknown"
                        status = status_module.get("overallStatus", "Unknown")
                        
                        by_phase[phase] = by_phase.get(phase, 0) + 1
                        by_status[status] = by_status.get(status, 0) + 1
                        
                        # Sponsors
                        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
                        lead_sponsor = sponsor_module.get("leadSponsor", {}).get("name")
                        if lead_sponsor:
                            sponsors.add(lead_sponsor)
                        
                        # Countries
                        locations = protocol.get("contactsLocationsModule", {}).get("locations", [])
                        for loc in locations:
                            if loc.get("country"):
                                countries.add(loc["country"])
                        
                        trials.append({
                            "nct_id": identification.get("nctId"),
                            "title": identification.get("briefTitle"),
                            "phase": phase,
                            "status": status,
                            "enrollment": status_module.get("enrollmentInfo", {}).get("count"),
                            "start_date": status_module.get("startDateStruct", {}).get("date"),
                            "primary_sponsor": lead_sponsor
                        })
                    
                    return {
                        "total_trials": len(studies),
                        "by_phase": by_phase,
                        "by_status": by_status,
                        "sponsors": list(sponsors)[:20],
                        "countries": list(countries)[:50],
                        "trial_details": trials
                    }
        except Exception as e:
            return {"total_trials": 0, "error": str(e), "trials": []}
    
    def _aggregate_patents(self, patent_details: Dict, inpi_patents: Dict) -> List[Dict]:
        """Aggregate patents from all sources"""
        
        all_patents = {}
        
        # Add WO patents
        for patent in patent_details.get("patents", []):
            pub_num = patent.get("publication_number")
            if pub_num:
                all_patents[pub_num] = patent
        
        # Add BR patents from INPI
        for patent in inpi_patents.get("br_patents", []):
            pub_num = patent.get("publication_number")
            if pub_num and pub_num not in all_patents:
                all_patents[pub_num] = patent
        
        return list(all_patents.values())
    
    def _build_executive_summary(
        self,
        molecule: str,
        pubchem_data: Dict,
        all_patents: List[Dict],
        fda_data: Dict,
        clinical_data: Dict
    ) -> Dict:
        """Build executive summary"""
        
        # Count jurisdictions
        jurisdictions = {}
        for patent in all_patents:
            jurisdiction = patent.get("jurisdiction", "Unknown")
            if jurisdiction:
                jurisdictions[jurisdiction] = jurisdictions.get(jurisdiction, 0) + 1
        
        return {
            "molecule_name": molecule,
            "generic_name": pubchem_data.get("iupac_name", "")[:100],
            "commercial_name": molecule.title(),
            "cas_number": pubchem_data.get("cas_number"),
            "dev_codes": pubchem_data.get("dev_codes", [])[:10],
            "total_patents": len(all_patents),
            "total_families": 0,  # TODO: Implement family counting
            "jurisdictions": {
                "brazil": jurisdictions.get("BR", 0),
                "usa": jurisdictions.get("US", 0),
                "europe": jurisdictions.get("EP", 0),
                "japan": jurisdictions.get("JP", 0),
                "china": jurisdictions.get("CN", 0),
                "wipo": jurisdictions.get("WO", 0)
            },
            "fda_status": fda_data.get("approval_status", "Unknown"),
            "clinical_trials_count": clinical_data.get("total_trials", 0),
            "consistency_score": 1.0  # TODO: Implement scoring
        }


# Singleton instance
pipeline_service = PipelineService()
